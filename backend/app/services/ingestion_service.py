import csv
import io
from datetime import datetime, date, timezone
from typing import List, Dict, Any, Tuple, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.product import Product
from app.models.store import Store
from app.models.sales import Sales
from app.schemas.data_ingestion import (
    RowValidationError,
    DataUploadErrorResponse,
    DataUploadSuccessResponse,
)

REQUIRED_COLUMNS = {"date", "sku_code", "store_id", "units_sold", "revenue"}


class SalesDataIngestionService:
    """High-performance atomic CSV ingestion pipeline with detailed validation."""

    def __init__(self, db: Session):
        self.db = db

    def process_csv(self, file_content: bytes) -> Tuple[bool, Any]:
        """
        Validate and ingest sales CSV content.
        Returns: (is_success: bool, response_payload: Union[DataUploadSuccessResponse, DataUploadErrorResponse])
        """
        # 1. Decode CSV content
        try:
            text_stream = io.StringIO(file_content.decode("utf-8-sig"))
        except UnicodeDecodeError:
            try:
                text_stream = io.StringIO(file_content.decode("latin-1"))
            except Exception as e:
                return False, DataUploadErrorResponse(
                    error_count=1,
                    errors=[
                        RowValidationError(
                            row_number=1,
                            column=None,
                            issue=f"Invalid file encoding: {str(e)}",
                        )
                    ],
                )

        reader = csv.DictReader(text_stream)
        if not reader.fieldnames:
            return False, DataUploadErrorResponse(
                error_count=1,
                errors=[
                    RowValidationError(
                        row_number=1,
                        column=None,
                        issue="Empty CSV file or missing header row.",
                    )
                ],
            )

        # Normalize column header names
        fieldnames = [f.strip() for f in reader.fieldnames if f]
        field_set = set(fieldnames)

        # 2. Check for missing required columns
        missing_columns = REQUIRED_COLUMNS - field_set
        if missing_columns:
            return False, DataUploadErrorResponse(
                error_count=len(missing_columns),
                errors=[
                    RowValidationError(
                        row_number=1,
                        column=col,
                        issue=f"Required column '{col}' is missing in CSV headers.",
                    )
                    for col in sorted(list(missing_columns))
                ],
            )

        # 3. Pre-fetch existing Products and Stores for O(1) lookup
        products = self.db.query(Product.id, Product.sku_code).all()
        sku_to_id_map: Dict[str, int] = {p.sku_code: p.id for p in products}

        stores = self.db.query(Store.id).all()
        valid_store_ids: Set[int] = {s.id for s in stores}

        # 4. Pre-fetch existing Sales unique keys to check for duplicates
        existing_sales_keys: Set[Tuple[int, int, date]] = set(
            self.db.query(Sales.product_id, Sales.store_id, Sales.date).all()
        )

        validation_errors: List[RowValidationError] = []
        parsed_records: List[Dict[str, Any]] = []
        seen_in_file: Set[Tuple[str, int, date]] = set()

        min_date: Optional[date] = None
        max_date: Optional[date] = None
        affected_product_ids: Set[int] = set()
        affected_store_ids: Set[int] = set()

        now_utc = datetime.now(timezone.utc)

        # Iterate rows (1-indexed CSV line count, line 1 is header, data starts at line 2)
        for line_num, raw_row in enumerate(reader, start=2):
            # Clean row values
            row = {k.strip(): (v.strip() if v is not None else "") for k, v in raw_row.items() if k}

            # Check required fields are present and not empty
            row_has_fatal_error = False

            raw_date = row.get("date", "")
            raw_sku = row.get("sku_code", "")
            raw_store = row.get("store_id", "")
            raw_units = row.get("units_sold", "")
            raw_rev = row.get("revenue", "")

            # Check Date
            parsed_date: Optional[date] = None
            if not raw_date:
                validation_errors.append(
                    RowValidationError(
                        row_number=line_num,
                        column="date",
                        issue="Date field cannot be empty.",
                        raw_value=raw_date,
                    )
                )
                row_has_fatal_error = True
            else:
                for date_format in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d-%m-%Y"):
                    try:
                        parsed_date = datetime.strptime(raw_date, date_format).date()
                        break
                    except ValueError:
                        continue
                if parsed_date is None:
                    validation_errors.append(
                        RowValidationError(
                            row_number=line_num,
                            column="date",
                            issue=f"Invalid date format '{raw_date}'. Expected format: YYYY-MM-DD.",
                            raw_value=raw_date,
                        )
                    )
                    row_has_fatal_error = True

            # Check SKU Code
            product_id: Optional[int] = None
            if not raw_sku:
                validation_errors.append(
                    RowValidationError(
                        row_number=line_num,
                        column="sku_code",
                        issue="SKU code cannot be empty.",
                        raw_value=raw_sku,
                    )
                )
                row_has_fatal_error = True
            elif raw_sku not in sku_to_id_map:
                validation_errors.append(
                    RowValidationError(
                        row_number=line_num,
                        column="sku_code",
                        issue=f"Unknown SKU code '{raw_sku}'. Product does not exist in database.",
                        raw_value=raw_sku,
                    )
                )
                row_has_fatal_error = True
            else:
                product_id = sku_to_id_map[raw_sku]

            # Check Store ID
            parsed_store_id: Optional[int] = None
            if not raw_store:
                validation_errors.append(
                    RowValidationError(
                        row_number=line_num,
                        column="store_id",
                        issue="Store ID cannot be empty.",
                        raw_value=raw_store,
                    )
                )
                row_has_fatal_error = True
            else:
                try:
                    parsed_store_id = int(raw_store)
                    if parsed_store_id not in valid_store_ids:
                        validation_errors.append(
                            RowValidationError(
                                row_number=line_num,
                                column="store_id",
                                issue=f"Unknown store ID '{raw_store}'. Store does not exist in database.",
                                raw_value=raw_store,
                            )
                        )
                        row_has_fatal_error = True
                except ValueError:
                    validation_errors.append(
                        RowValidationError(
                            row_number=line_num,
                            column="store_id",
                            issue=f"Invalid store ID '{raw_store}'. Must be an integer.",
                            raw_value=raw_store,
                        )
                    )
                    row_has_fatal_error = True

            # Check Units Sold
            parsed_units: Optional[int] = None
            if not raw_units:
                validation_errors.append(
                    RowValidationError(
                        row_number=line_num,
                        column="units_sold",
                        issue="Units sold cannot be empty.",
                        raw_value=raw_units,
                    )
                )
                row_has_fatal_error = True
            else:
                try:
                    parsed_units = int(raw_units)
                    if parsed_units < 0:
                        validation_errors.append(
                            RowValidationError(
                                row_number=line_num,
                                column="units_sold",
                                issue=f"Negative units sold '{raw_units}' is not allowed.",
                                raw_value=raw_units,
                            )
                        )
                        row_has_fatal_error = True
                except ValueError:
                    validation_errors.append(
                        RowValidationError(
                            row_number=line_num,
                            column="units_sold",
                            issue=f"Invalid units sold '{raw_units}'. Must be an integer.",
                            raw_value=raw_units,
                        )
                    )
                    row_has_fatal_error = True

            # Check Revenue
            parsed_revenue: Optional[float] = None
            if not raw_rev:
                validation_errors.append(
                    RowValidationError(
                        row_number=line_num,
                        column="revenue",
                        issue="Revenue cannot be empty.",
                        raw_value=raw_rev,
                    )
                )
                row_has_fatal_error = True
            else:
                try:
                    parsed_revenue = float(raw_rev)
                    if parsed_revenue < 0:
                        validation_errors.append(
                            RowValidationError(
                                row_number=line_num,
                                column="revenue",
                                issue=f"Negative revenue '{raw_rev}' is not allowed.",
                                raw_value=raw_rev,
                            )
                        )
                        row_has_fatal_error = True
                except ValueError:
                    validation_errors.append(
                        RowValidationError(
                            row_number=line_num,
                            column="revenue",
                            issue=f"Invalid revenue '{raw_rev}'. Must be a valid number.",
                            raw_value=raw_rev,
                        )
                    )
                    row_has_fatal_error = True

            # Duplicate Checks (if all key fields were parseable)
            if not row_has_fatal_error and parsed_date and product_id and parsed_store_id:
                file_key = (raw_sku, parsed_store_id, parsed_date)
                if file_key in seen_in_file:
                    validation_errors.append(
                        RowValidationError(
                            row_number=line_num,
                            column=None,
                            issue=f"Duplicate record in uploaded file for SKU '{raw_sku}', Store {parsed_store_id}, Date {parsed_date}.",
                        )
                    )
                else:
                    seen_in_file.add(file_key)

                # Record date range
                if min_date is None or parsed_date < min_date:
                    min_date = parsed_date
                if max_date is None or parsed_date > max_date:
                    max_date = parsed_date

                affected_product_ids.add(product_id)
                affected_store_ids.add(parsed_store_id)

                parsed_records.append(
                    {
                        "product_id": product_id,
                        "store_id": parsed_store_id,
                        "date": parsed_date,
                        "units_sold": parsed_units,
                        "revenue": parsed_revenue,
                        "promotion_id": None,
                        "created_at": now_utc,
                        "updated_at": now_utc,
                    }
                )

        # 5. If ANY validation errors exist, reject entire batch (atomic)
        if validation_errors:
            return False, DataUploadErrorResponse(
                error_count=len(validation_errors),
                errors=validation_errors,
            )

        if not parsed_records:
            return False, DataUploadErrorResponse(
                error_count=1,
                errors=[
                    RowValidationError(
                        row_number=1,
                        column=None,
                        issue="No valid data rows found in CSV.",
                    )
                ],
            )

        # 6. Bulk Upsert (replace any existing records in range, then bulk insert new records)
        try:
            # 1 single fast batch delete for all affected product/store/date ranges
            if min_date and max_date and affected_product_ids and affected_store_ids:
                self.db.query(Sales).filter(
                    Sales.product_id.in_(list(affected_product_ids)),
                    Sales.store_id.in_(list(affected_store_ids)),
                    Sales.date >= min_date,
                    Sales.date <= max_date
                ).delete(synchronize_session=False)

            # Use bulk_insert_mappings for high throughput
            batch_size = 1000
            for i in range(0, len(parsed_records), batch_size):
                batch = parsed_records[i : i + batch_size]
                self.db.bulk_insert_mappings(Sales, batch)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            return False, DataUploadErrorResponse(
                error_count=1,
                errors=[
                    RowValidationError(
                        row_number=1,
                        column=None,
                        issue=f"Database transaction error during bulk insert: {str(e)}",
                    )
                ],
            )

        # 7. Return success response
        date_range_info = None
        if min_date and max_date:
            date_range_info = {
                "start_date": min_date.isoformat(),
                "end_date": max_date.isoformat(),
            }

        return True, DataUploadSuccessResponse(
            total_rows=len(parsed_records),
            inserted_rows=len(parsed_records),
            date_range=date_range_info,
            background_job_triggered=True,
        )

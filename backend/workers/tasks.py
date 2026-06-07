from core.celery_app import celery_app
from services.reporting.export_engine import ExportEngine
import time

@celery_app.task(bind=True, name="generate_fir_pdf_task")
def generate_fir_pdf_task(self, case_id: str, case_data: dict, transactions: list):
    """
    Background task to generate a complex FIR PDF.
    """
    # Simulate heavy processing time
    time.sleep(5)
    
    # Generate the actual PDF bytes
    # Note: ExportEngine handles DB data if needed, but here we pass data directly to avoid async DB issues in sync Celery tasks
    pdf_bytes = ExportEngine.generate_fir_pdf(case_id, case_data, transactions)
    
    # Returning the bytes directly in Celery results isn't optimal for large files, 
    # but for this MVP, we return it as a hex string to avoid JSON serialization errors with raw bytes.
    return pdf_bytes.hex()

@celery_app.task(bind=True, name="generate_charge_sheet_task")
def generate_charge_sheet_task(self, case_id: str, case_data: dict, transactions: list):
    """
    Background task to generate a complex DOCX Charge Sheet.
    """
    time.sleep(5)
    
    docx_bytes = ExportEngine.generate_charge_sheet_docx(case_id, case_data, transactions)
    return docx_bytes.hex()

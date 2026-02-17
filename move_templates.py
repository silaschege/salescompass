import os
import shutil

SOURCE_DIR = r"c:\Users\User\Documents\GitHub\salescompass-main\core\billing\templates\billing"
DEST_DIR = r"c:\Users\User\Documents\GitHub\salescompass-main\core\invoicing\templates\invoicing"
FILES_TO_MOVE = [
    "invoice_list.html", "invoice_create.html", "invoice_detail.html", "invoice_form.html",
    "invoice_print.html", "invoice_pdf.html", 
    "payment_list.html", "payment_form.html", "payment_detail.html",
    "payment_method_list.html", "payment_method_form.html",
    "credit_adjustment_list.html", "credit_adjustment_form.html",
    "adjustment_type_list.html", "adjustment_type_form.html",
    "payment_provider_list.html", "payment_provider_form.html",
    "payment_type_list.html", "payment_type_form.html",
    "dunning_management.html", "failed_payments.html",
    "reconciliation.html", "tenant_billing_search.html",
    "billing_history.html", "tenant_payment_config.html",
    "invoice_generation.html", "invoice_overdue_list.html",
    "invoice_paid_list.html", "invoice_void_list.html",
    "payment_gateway_list.html", "payment_gateway_form.html", "payment_gateway_config.html",
    "credit_adjustment_management.html", "credit_adjustment_confirm_delete.html",
    "payment_method_confirm_delete.html",
    "payment_provider_config_list.html", "payment_provider_config_form.html", "payment_provider_config_confirm_delete.html",
    "payment_provider_confirm_delete.html", "payment_type_confirm_delete.html",
    "adjustment_type_confirm_delete.html", "invoice_confirm_delete.html", "payment_confirm_delete.html"
]

os.makedirs(DEST_DIR, exist_ok=True)

for params in FILES_TO_MOVE:
    src = os.path.join(SOURCE_DIR, params)
    dst = os.path.join(DEST_DIR, params)
    if os.path.exists(src):
        print(f"Moving {src} to {dst}")
        try:
            shutil.move(src, dst)
            
            # Now replace content
            with open(dst, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Replace URLs
            new_content = content.replace('billing:invoice', 'invoicing:invoice')
            new_content = new_content.replace('billing:payment', 'invoicing:payment')
            new_content = new_content.replace('billing:credit', 'invoicing:credit')
            new_content = new_content.replace('billing:adjustment', 'invoicing:adjustment')
            new_content = new_content.replace('billing:dunning', 'invoicing:dunning')
            new_content = new_content.replace('billing:failed', 'invoicing:failed')
            new_content = new_content.replace('billing:tenant_billing', 'invoicing:tenant_billing')
            new_content = new_content.replace('billing:billing_history', 'invoicing:billing_history')
            new_content = new_content.replace('billing:tenant_payment', 'invoicing:tenant_payment')
            new_content = new_content.replace('billing:reconciliation', 'invoicing:reconciliation')
            new_content = new_content.replace('billing:payment_gateway', 'invoicing:payment_gateway')
            new_content = new_content.replace('billing:payment_method', 'invoicing:payment_method')
            new_content = new_content.replace('billing:payment_provider', 'invoicing:payment_provider')
            new_content = new_content.replace('billing:payment_type', 'invoicing:payment_type')
            
            # Also 'extends "billing/base.html"' -> 'extends "invoicing/base.html"'
            new_content = new_content.replace('billing/base.html', 'invoicing/base.html')
            
            with open(dst, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except Exception as e:
            print(f"Error processing {src}: {e}")
    else:
        print(f"File not found: {src}")

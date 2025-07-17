from flask import Flask, request, jsonify
import hashlib
import hmac
import json
from backend import db

app = Flask(__name__)

# Replace with your Gumroad webhook secret
GUMROAD_SECRET = "your_gumroad_webhook_secret"

@app.route('/gumroad-webhook', methods=['POST'])
def gumroad_webhook():
    if request.method == 'POST':
        # Verify the webhook signature
        # This is a crucial security step to ensure the request comes from Gumroad
        # and has not been tampered with.
        # Gumroad sends an X-Gumroad-Signature header with a SHA256 HMAC signature
        # of the request body, using your webhook secret.
        signature = request.headers.get('X-Gumroad-Signature')
        if not signature:
            return jsonify({"message": "No signature provided"}), 403

        payload = request.get_data()
        calculated_signature = hmac.new(GUMROAD_SECRET.encode('utf-8'),
                                        payload,
                                        hashlib.sha256).hexdigest()

        if not hmac.compare_digest(calculated_signature, signature):
            return jsonify({"message": "Invalid signature"}), 403

        data = request.form.to_dict()
        event_name = data.get('event')

        if event_name == 'sale':
            product_name = data.get('product_name')
            seller_email = data.get('seller_email')
            customer_email = data.get('email')
            licence_key = data.get('licence_key')

            user = db.get_user_by_email(customer_email)
            if user:
                paid_plans = json.loads(user['paid_plans'])
                # Map Gumroad product names to internal plan names
                if "1er semestre" in product_name:
                    paid_plans["1er semestre"] = True
                elif "2eme semestre" in product_name:
                    paid_plans["2eme semestre"] = True
                elif "annee complete" in product_name:
                    paid_plans["annee complete"] = True
                
                db.update_user_paid_plans(user['id'], paid_plans)
                print(f"Updated user {customer_email} with new plans: {paid_plans}")
            else:
                print(f"User {customer_email} not found in DB. Cannot update plans.")

        return jsonify({"message": "Webhook received"}), 200

if __name__ == '__main__':
    db.init_db()
    app.run(host='0.0.0.0', port=5000)

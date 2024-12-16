from flask import Flask, request, jsonify, send_file
import psycopg2
import csv
import io

app = Flask(__name__)

# Establish PostgreSQL connection
def get_db_connection():
    conn = psycopg2.connect(
        host="192.168.10.92",
        port="5432",
        database="ICubeTransactionTemp",
        user="postgres",
        password="Admin@123"
    )
    return conn

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()  # Parse the incoming request from Dialogflow

    # Get the intent name
    intent_name = req['queryResult']['intent']['displayName']

    # Check the intent and handle accordingly
    if intent_name == "procurement_submodule":
        # Extract parameters from the request
        parameters = req['queryResult']['parameters']
        report_type = parameters.get('procurement_report')
        date_range = parameters.get('date-period')

        # Extract the start and end dates
        start_date = date_range[0]['startDate']
        end_date = date_range[0]['endDate']

        # Map the report type to the PostgreSQL function
        if report_type == "Purchase By Supplier -GRN":
            report_function = "fn_purchase_purchase_return"
        else:
            # Handle other report types if necessary
            return jsonify({"fulfillmentText": "Invalid report type."})

        # Call the PostgreSQL function to get the report data
        try:
            # Establish connection to the PostgreSQL database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Execute the PostgreSQL function (ensure that it's properly defined in your database)
            cursor.execute(f"SELECT * FROM {report_function}(%s, %s)", (start_date, end_date))
            rows = cursor.fetchall()

            # Prepare CSV response
            output = io.StringIO()
            csv_writer = csv.writer(output)
            # Write the headers, you can adjust based on your function's output
            csv_writer.writerow([desc[0] for desc in cursor.description])
            csv_writer.writerows(rows)

            # Reset StringIO cursor to the beginning
            output.seek(0)

            # Send CSV as a downloadable file
            return send_file(output, mimetype='text/csv', as_attachment=True, download_name=f"{report_type}_report.csv")

        except Exception as e:
            # Log the error for debugging
            print(f"Error: {e}")

            # Return an error message to Dialogflow
            return jsonify({
                "fulfillmentText": "I encountered an issue generating your report.... Please try again later."
            })

    else:
        # Fallback for unsupported intents
        return jsonify({
            "fulfillmentText": "I didn't understand that request. Can you try again?"
        })

# Start the Flask server
if __name__ == '__main__':
    app.run(port=5000, debug=True)

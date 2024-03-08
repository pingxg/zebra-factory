import csv
import os

# Path to your CSV file
csv_file_path = 'vk11.csv'

# Start of the SQL statement
sql = "INSERT INTO data.salmon_orders (date, product, customer, quantity, price) VALUES "

# Check if the file exists
if not os.path.isfile(csv_file_path):
    print(f"File {csv_file_path} does not exist.")
else:
    try:
        # Read the CSV file and generate SQL for each row
        with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            sql_values = []
            for row in reader:
                # Access data by column name
                date = row['date']
                product = row['product']
                customer = row['customer']
                quantity = row['quantity']
                price = row['price']
                
                # Use parameterized queries
                value = f"('{date}', '{product}', '{customer}', {quantity}, {price})"
                sql_values.append(value)

        # Combine all SQL parts and add a final semicolon
        sql += ",\n".join(sql_values) + ";"

        # Output the complete SQL statement
        print(sql)
    except Exception as e:
        print(f"An error occurred: {e}")
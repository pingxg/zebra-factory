import csv

# Path to your CSV file
csv_file_path = 'vk01.csv'



# Start of the SQL statement
sql = "INSERT INTO data.salmon_orders (date, product, customer, quantity, price) VALUES "

# Read the CSV file and generate SQL for each row
with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile, delimiter=';')
    next(reader)  # Skip the header row
    sql_values = []
    for row in reader:
        date, product, customer, quantity, price = row
        # date = date.split("/")[2]+"-"+date.split("/")[1]+"-"+date.split("/")[0]
        value = f"('{date}', '{product}', '{customer}', {quantity}, {price})"
        sql_values.append(value)

# Combine all SQL parts and add a final semicolon
sql += ",\n".join(sql_values) + ";"

# Output the complete SQL statement
print(sql)

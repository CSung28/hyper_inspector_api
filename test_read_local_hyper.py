from app.services.hyper_reader import (
    get_row_count,
    get_table_schema,
    list_tables,
    preview_table,
)

hyper_path = r"C:\Users\LG\Desktop\Sample - Superstore.hyper"

tables = list_tables(hyper_path)
print("tables:")
print(tables)

table = tables[0]

print("\nschema:")
print(get_table_schema(hyper_path, table))

print("\nrow count:")
print(get_row_count(hyper_path, table))

print("\npreview:")
print(preview_table(hyper_path, table, limit=10))

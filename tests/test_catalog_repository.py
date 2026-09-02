from database.repositories.catalog_repository import normalize_dataset_key


def test_dataset_key_is_case_insensitive():
    assert normalize_dataset_key("Customers.CSV") == "customers.csv"
    assert normalize_dataset_key("customers.csv") == "customers.csv"


def test_dataset_key_removes_external_path_components():
    assert (
        normalize_dataset_key(r"..\..\Customer_Data.CSV")
        == "customer_data.csv"
    )

    assert (
        normalize_dataset_key("../../Customer_Data.CSV")
        == "customer_data.csv"
    )
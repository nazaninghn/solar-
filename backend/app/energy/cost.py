def calculate_energy_cost(
    grid_import_kwh: float,
    grid_export_kwh: float,
    buy_price: float,
    sell_price: float,
):
    import_cost = grid_import_kwh * buy_price
    export_revenue = grid_export_kwh * sell_price

    net_cost = import_cost - export_revenue

    return {
        "import_cost": import_cost,
        "export_revenue": export_revenue,
        "net_cost": net_cost,
    }

def is_low_stock(medication):
    return medication.quantity <= medication.minimum_quantity

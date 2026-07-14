export interface OrderLine {
  snackStableId: number;
  quantity: number;
}

export function createOrderLine(snackStableId: number, quantity: number): OrderLine {
  const line: OrderLine = {
    snackStableId: snackStableId,
    quantity: quantity
  };
  return line;
}

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

const _originalSelectInstallmentPlanForLine =
  PaymentScreen.prototype._selectInstallmentPlanForLine ||
  async function () {
    return { confirmed: true, payload: null };
  };

patch(PaymentScreen.prototype, {
  _getLinkedSaleOrderId() {
    try {
      const order = this.currentOrder;
      if (!order) return null;
      const lines = order.get_orderlines ? order.get_orderlines() : [];
      for (const line of lines) {
        if (line.sale_order_origin_id && line.sale_order_origin_id.id) {
          return line.sale_order_origin_id.id;
        }
      }
      return null;
    } catch (e) {
      return null;
    }
  },

  async _saleOrderHasInstallmentTerm(saleOrderId) {
    try {
      const result = await this.orm.read(
        "sale.order",
        [saleOrderId],
        ["installment_term_id"],
      );
      const record = result && result[0];
      if (!record) return false;
      const termField = record.installment_term_id;
      const hasTerm = !!(termField && termField !== false);

      return hasTerm;
    } catch (e) {
      console.log(e);
      return false;
    }
  },

  async _selectInstallmentPlanForLine(paymentline, paymentMethodId) {
    const saleOrderId = this._getLinkedSaleOrderId();

    if (saleOrderId) {
      const hasTerm = await this._saleOrderHasInstallmentTerm(saleOrderId);
      if (hasTerm) {
        return { confirmed: true, payload: null };
      }
    }

    return await _originalSelectInstallmentPlanForLine.call(
      this,
      paymentline,
      paymentMethodId,
    );
  },
});

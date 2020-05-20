import React, { useState, useEffect } from 'react';
import config from '../../config';
import ProductDisabler from '../../components/ProductDisabler';
import useAction from '../../hooks/useAction';
import {
  getDisabledProducts,
  disableProduct,
  enableProduct,
} from '../../components/api';

export default function Footer() {
  const [disabledProducts, setDisabledProducts] = useState([]);
  const [getDisabledProductsState, getDisabledProductsAction] = useAction(
    getDisabledProducts
  );
  const [disableProductState, disableProductAction] = useAction(disableProduct);
  const [enableProductState, enableProductAction] = useAction(enableProduct);
  const loading =
    getDisabledProductsState.loading ||
    disableProductState.loading ||
    enableProductState.loading;
  const error =
    getDisabledProductsState.error ||
    disableProductState.error ||
    enableProductState.error;
  const init = async () => {
    const disabledProducts = await getDisabledProductsAction();

    setDisabledProducts(disabledProducts.data);
  };

  useEffect(() => {
    init();
  }, []);

  const handleStateChange = async productBranch => {
    if (productBranch.disabled) {
      await enableProductAction(productBranch.product, productBranch.branch);
    } else {
      await disableProductAction(productBranch.product, productBranch.branch);
    }

    await init();
  };

  return (
    <ProductDisabler
      productBranches={config.PRODUCTS.flatMap(product =>
        product.branches
          .filter(branch => branch.disableable)
          .map(pb => ({
            product: product.product,
            branch: pb.branch,
            prettyProduct: product.prettyName,
            prettyBranch: pb.prettyName,
            disabled:
              product.product in disabledProducts &&
              disabledProducts[product.product].includes(pb.branch),
          }))
      )}
      onStateChange={handleStateChange}
      loading={loading}
      error={error}
    />
  );
}

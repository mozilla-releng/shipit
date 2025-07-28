import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router';
import {
  disableProduct,
  enableProduct,
  getDisabledProducts,
} from '../../components/api';
import ProductDisabler from '../../components/ProductDisabler';
import config from '../../config';
import useAction from '../../hooks/useAction';

export default function Footer() {
  const location = useLocation();
  const group = new URLSearchParams(location.search).get('group') || 'firefox';
  const [disabledProducts, setDisabledProducts] = useState([]);
  const [getDisabledProductsState, getDisabledProductsAction] =
    useAction(getDisabledProducts);
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

  const handleStateChange = async (productBranch) => {
    if (productBranch.disabled) {
      await enableProductAction(productBranch.product, productBranch.branch);
    } else {
      await disableProductAction(productBranch.product, productBranch.branch);
    }

    await init();
  };

  return (
    <ProductDisabler
      productBranches={config.PRODUCTS[group].flatMap((product) =>
        product.branches
          .filter((branch) => branch.disableable)
          .map((pb) => ({
            product: product.product,
            branch: pb.branch,
            prettyProduct: product.prettyName,
            prettyBranch: pb.prettyName,
            disabled:
              product.product in disabledProducts &&
              disabledProducts[product.product].includes(pb.branch),
          })),
      )}
      onStateChange={handleStateChange}
      loading={loading}
      error={error}
    />
  );
}

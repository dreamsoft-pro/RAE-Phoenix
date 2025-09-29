angular.module('digitalprint.services')
    .factory('CalcSimplifyWidgetService', function ($q) {

        function checkFormatExclusions(product,format) {

            var def = $q.defer();

            if (!product.currentFormat) {
                def.reject('no product.currentFormat')
                return def.promise;
            }
            product.formatExcluded = [];

            _.each(product.attributes, function (attribute, attributeIndex) {

                if( !attribute.options && (product.attributes.length - 1) === attributeIndex ) {
                    def.resolve(true);
                }

                _.each(attribute.options, function (option, optionIndex) {

                    if (option && option.formats) {
                        if (!_.includes(option.formats, product.currentFormat.ID)) {
                            product.formatExcluded.push(option.ID);
                            if (product.selectedOptions[attribute.attrID] === option.ID) {
                                delete product.selectedOptions[attribute.attrID];
                            }
                        }
                    }

                    if( (product.attributes.length - 1) === attributeIndex && (attribute.options.length - 1) === optionIndex ) {
                        def.resolve(true)
                    }
                });
            });

            return def.promise;

        }

        function removeUnActiveOptions(product) {

            var def = $q.defer();

            var index = 0;
            _.each(product.attributeMap, function (attrID) {

                var attributeIndex = _.findIndex(product.attributes, {attrID: attrID});

                if (product.selectedOptions[attrID] === undefined) {

                    if( (product.attributeMap.length-1) > index ) {
                        def.resolve(true)
                    }

                } else {

                    if(attributeIndex > -1) {
                        if( product.attributes[attributeIndex].filteredOptions.length === 0 ) {
                            delete product.selectedOptions[attrID];
                        }
                    }

                    if( (product.attributeMap.length-1) > index ) {
                        def.resolve(true)
                    }

                }

                index++;
            });

            return def.promise;
        }

        function markEmptyOptions(product) {

            var emptyOptions = [];
            _.each(product.selectedOptions, function (optID, attrID) {
                var idx = _.findIndex(product.attributes, {attrID: parseInt(attrID)});
                if (idx > -1 && product.attributes[idx].filteredOptions.length === 0) {
                    emptyOptions.push(optID);
                }
            })

            return emptyOptions
        }

        function removeEmptyOptionFromSelected(product, newProduct) {

            var def = $q.defer();
            var emptyOptions=markEmptyOptions(product)
            _.each(product.selectedOptions, function (optID, attrID) {
                if (!optID) {
                    console.log('Lack of optID: ', optID);
                    console.log('attrID is:', attrID);
                }else if (!_.includes(emptyOptions, optID)) {
                    newProduct.options.push({
                        attrID: parseInt(attrID),
                        optID: optID
                    });
                }
            })
        }

        function prepareProductPromise(scope, newItem) {

            var def = $q.defer();

            newItem.products = [];
            _.each(scope.complexProducts, function (complexProduct, index) {

                var product = complexProduct.selectedProduct.data;

                var newProduct = {};

                newProduct.groupID = product.info.groupID;
                newProduct.typeID = product.info.typeID;
                newProduct.name = product.info.typeName;

                if (!product.currentFormat) {
                    console.error('Formats must be assign!');
                }

                newProduct.formatID = product.currentFormat.ID;

                if (!product.currentFormat.custom) {

                    newProduct.width = product.currentFormat.width;
                    newProduct.height = product.currentFormat.height;
                } else {
                    newProduct.width = product.currentFormat.customWidth + product.currentFormat.slope * 2;
                    newProduct.height = product.currentFormat.customHeight + product.currentFormat.slope * 2;
                }

                if (product.currentPages) {
                    newProduct.pages = product.currentPages;
                } else {
                    newProduct.pages = 2;
                }
                newProduct.options = [];

                removeEmptyOptionFromSelected(product, newProduct);

                newProduct.attrPages = product.attrPages;

                if (product.info.noCalculate !== true) {
                    newItem.products.push(newProduct);
                }

                if ((scope.complexProducts.length - 1) === index) {
                    def.resolve(newItem);
                }


            });

            return def.promise;
        }

        const showSumPrice = ($scope) =>{

            if (angular.isDefined($scope.calculation)) {
                let price = _.parseFloat($scope.calculation.priceTotal)

                if ($scope.calculation.deliveryPrice) {
                    price += _.parseFloat($scope.calculation.deliveryPrice)
                }

                $scope.net_per_pcs = (price / $scope.calculation.volume).toFixed(2).replace('.', ',');

                return price.toFixed(2).replace('.', ',')

            } else {
                return ''
            }
        }

        const showSumGrossPrice = ($scope) =>{

            if (angular.isDefined($scope.calculation)) {
                let price = _.parseFloat($scope.calculation.priceTotalBrutto)

                if ($scope.calculation.deliveryGrossPrice) {
                    price += _.parseFloat($scope.calculation.deliveryGrossPrice)
                }

                $scope.gross_per_pcs = (price / $scope.calculation.volume).toFixed(2).replace('.', ',');

                return price.toFixed(2).replace('.', ',')

            } else {
                return ''
            }
        }

        return {
            removeEmptyOptionFromSelected,
            checkFormatExclusions,
            removeUnActiveOptions,
            prepareProductPromise,
            showSumPrice,
            showSumGrossPrice
        };

    });

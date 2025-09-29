'use strict';

angular.module('dpClient.app')
    .controller('index.AttributeDetails', function ($scope, $window, $stateParams, $filter, AttributeFiltersService, Notification) {

        console.log($stateParams);
        $scope.option = {};
        $scope.products = [];

        function createFilterPart(items, name, type, filterConfig, label, hidden, precision) {
            items = _.clone(items);
            var item = { name: name, type: type, title: !!label ? label : name, hidden: hidden };
            switch (type) {
                case 'multi-select':
                case 'multi-select-color':
                    item.values = filterConfig[name].values;
                    item.selectedValues = {};
                    break;
                case 'range':
                    item.minValue = filterConfig[name].minValue;
                    item.maxValue = filterConfig[name].maxValue;
                    var diff = filterConfig[name].maxValue - filterConfig[name].minValue
                    var step = 1
                    if (diff < 1) {
                        step = 0.01;
                    } else if (diff < 10) {
                        step = 0.1;
                    } else if (diff < 100) {
                        step = 1
                    } else {
                        step = Math.round(diff / 50);
                    }
                    item.options = {
                        floor: filterConfig[name].minValue,
                        ceil: filterConfig[name].maxValue,
                        step: step,
                        precision: precision,
                        onChange: function () {
                            $scope.onInputChange.apply(this)
                        }
                    }
                    break;
            }
            items.push(item);
            return items;
        };

        var sendData = {};
        sendData.attrID = $stateParams.attrid;
        sendData.optID = $stateParams.optid;
        AttributeFiltersService.getOption(sendData).then(function (data) {
            if (data.length !== 0) {
                console.log(data);

                $scope.option.name = data[0].name;
                $scope.option.sizePage = data[0].sizePage;
                $scope.option.descriptions = data[0].descriptions;

                $scope.option.certificates = [];
                var certs = data[0].descriptions.certificates.split(', ');
                if (certs.length > 0) {
                    $scope.option.certificates = certs;
                }

                $scope.option.printingTechniques = [];
                var printingTechniques = data[0].descriptions.printingTechniques.split(', ');
                if (printingTechniques.length > 0) {
                    $scope.option.printingTechniques = printingTechniques;
                }

                $scope.option.finishingAndProcessing = [];
                var finishingAndProcessing = data[0].descriptions.finishingAndProcessing.split(', ');
                if (finishingAndProcessing.length > 0) {
                    $scope.option.finishingAndProcessing = finishingAndProcessing;
                }

                AttributeFiltersService.getProductsUsingOptions(sendData.attrID).then(function (allProducts) {
                    if (allProducts.length > 0) {
                        $scope.products = _.filter(allProducts, function (product) {
                            for (var i = 0; i < product.options.length; i++) {
                                if (product.options[i] == data[0].ID) {
                                    return true;
                                }
                            }
                            return false;
                        });
                    }
                }, function (error) {

                });

                // get alt papers
                var dataSend = {};
                dataSend.attrID = 2;
                dataSend.optID = data[0].ID;
                $scope.alternativePapers = [];
                AttributeFiltersService.getRelativePapers(dataSend).then(function (altPapersFilter) {
                    if (altPapersFilter.length > 0) {
                        AttributeFiltersService.getAttributeFilters(dataSend.attrID)
                            .then(function (filterConfigData) {
                                var filterConfig = filterConfigData.filterConfig;
                                var filterPartsAltPapers = [];
                                filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'name', 'text', filterConfig, 'name_of_atrritute');
                                filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'category', 'select', filterConfig);
                                filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'group', 'select', filterConfig);
                                filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'paper_type', 'select', filterConfig);
                                filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'weight', 'range', filterConfig, null, false, 0);
                                filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'whiteness', 'range', filterConfig, null, false, 0);
                                filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'thickness', 'range', filterConfig, null, false, 3);
                                filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'opacity', 'range', filterConfig, null, false, 0);
                                filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'roughness', 'range', filterConfig, null, false, 0);
                                filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'certificates', 'multi-select', filterConfig);
                                filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'printingTechniques', 'multi-select', filterConfig);
                                filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'application', 'multi-select', filterConfig);
                                filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'color_hex', 'multi-select-color', filterConfig, 'paper_color');
                                _.each(altPapersFilter, function (fd) {
                                    var part = _.find(filterPartsAltPapers, { name: fd.name });
                                    if (fd.valueType == 'min') {
                                        part.minValue = fd.value;
                                    } else if (fd.valueType == 'max') {
                                        part.maxValue = fd.value;
                                    } else if (part.type == 'multi-select' || part.type == 'multi-select-color') {
                                        if (!part.selectedValues) {
                                            part.selectedValues = [];
                                        }
                                        part.selectedValues[fd.value] = true;
                                    } else if (fd.valueType == 'exact') {
                                        part.value = String(fd.value);
                                    }
                                });
                                AttributeFiltersService.search(2, filterPartsAltPapers).then(function (altPapers) {
                                    $scope.alternativePapers = altPapers;
                                });
                            });
                    }
                });

            }
        });

        $scope.downloadPDF = function(){
            console.log('started rendering');
            var downloadData = {};
            downloadData.optID  = $stateParams.optid;
            downloadData.altPapers = $scope.alternativePapers;
            AttributeFiltersService.downloadPDF(downloadData).then(function (downloadResponse) {
                console.log(downloadResponse);
                if(downloadResponse.success){
                    $window.open(downloadResponse.link, '_blank');
                }else{
                    Notification.error($filter('translate')('unexpected_error'));
                }
            });
        };

    });

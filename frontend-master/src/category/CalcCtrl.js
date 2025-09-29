'use strict';

angular.module('dpClient.app')
    .filter('alternativeOptions', function (useAlt) {
        return function (items) {
            return _.filter(items, function (item) {
                return useAlt ? true : !item.isAlternative
            });
        }
    })
    .controller('category.CalcCtrl', function ($scope, $rootScope, $config, $filter, $cookies, $timeout, $state,
                                               PsTypeService, PsGroupService, PsAttributeService, PsFormatService,
                                               PsPageService, PsComplexService, CalculationService, TaxService,
                                               PsTypeDescriptionService, $stateParams, Notification, AuthService,
                                               AuthDataService, DeliveryService, AddressService, DpCategoryService,
                                               DeliveryWidgetService, TemplateRootService, DpOrderService, TokenService,
                                               SettingService, localStorageService, $modal, $q, TextWidgetService,
                                               CountriesService, DomWidgetService, CalculateDataService, $window,
                                               AddressWidgetService, CalcSimplifyWidgetService, $sce, $location,
                                               MainWidgetService, CustomProductService, LoginWidgetService, DpCartsDataService, CommonService,
                                               FileUploader,
                                               ProductFileService,
                                               CalcFileService) {
        // TODO Remove fragment while transfer to webpack
        try {
            var log = anylogger('Calc');
        } catch (e) {
            var log = {
                info: function () {
                },
                debug: function () {
                }
            };
        }
        const timeouts=[]
        /**
         *
         * @param {Object} $scope
         */
        $scope.type = {};
        $scope.group = {};
        $scope.volumes = [];
        $scope.complexProducts = [];

        $scope.currentTypeID = null;
        $scope.currentGroupID = null;

        /**
         * @param $stateParams
         * @param $stateParams.typeurl
         * @param $stateParams.groupurl
         */
        var choosenPaperID = false;
        if ($stateParams.typeurl.includes('?paperID=')) {
            var splitType = $stateParams.typeurl.split('?paperID=');
            $scope.currentTypeUrl = splitType[0];
            choosenPaperID = splitType[1];
        } else {
            $scope.currentTypeUrl = $stateParams.typeurl;
        }
        $rootScope.$on('$stateChangeStart', function (event, toState, toParams, fromState, fromParams) {
            timeouts.forEach(timer=>$timeout.cancel(timer))
        });

        $scope.currentGroupUrl = $stateParams.groupurl;

        var countProducts;
        var productsLoaded = false;
        var stopSelect = undefined;
        var stopSelectAttr;
        var deletedAttrs = [];

        var AttributeService;
        var FormatService;
        var PagesService;
        var ComplexService;
        var CalculateService;

        var _timeout;

        $scope.editorUrl = '';
        $scope.currentType = {};
        $scope.realisationTimes = [];
        $scope.activeVolume = {};
        $scope.rememberVolume = {};
        $scope.customVolume = {};
        $scope.taxes = [];
        $scope.loadVolumes = false;
        $scope.summaryThickness = {};
        $scope.allThickness = 0;
        $scope.complexID = 0;
        $scope.productItem = {};
        $scope.hideAmount = true;
        $scope.deliveryLackOfVolume = 0;

        $scope.addresses = [];
        $scope.senders = [];
        $scope.productAddresses = [];
        $scope.deliveries = [];
        $scope.filteredDeliveries = [];
        $scope.technologies = [];
        $scope.optionPicture = {};
        $scope.query = {};

        // Galerie
        $scope.galleries = [];
        // Tekst
        $scope.descriptions = [];
        // Miniatura
        $scope.thumbnails = [];
        // makieta
        $scope.patterns = [];

        $scope.actualFile = null;

        $scope.showPattern = false;
        $scope.showSummary = true;

        $scope.calcFiles = [];
        $scope.calcFilesDisplay = [];
        $scope.isAddToCartDisabled = false;
        $scope.calcFilesSetID = null;
        $scope.calcFilesPaginationList = [{count: 10, name: '10'}, {count: 25, name: '25'}, {
            count: 50,
            name: '50'
        }, {count: 100, name: '100'}];
        $scope.calcFilesPerPage = 25;
        $scope.calcFilesCurrentPage = 1;

        $rootScope.$on('delivery', function (e, productAddresses) {

            if (angular.isDefined($scope.calculation)) {
                $scope.calculation.deliveryPrice = productAddresses[0].price;
                $scope.calculation.deliveryGrossPrice = productAddresses[0].priceGross;
            }
            $scope.productAddresses = _.clone(productAddresses)
        })

        $scope.$on('$stateChangeStart', (event, toState, toParams, fromState, fromParams) => {
            $rootScope.$emit('startPreLoader');
        })

        $scope.calcFilesLoading = {
            isBW: false,
            isSepia: false,
            removeFilters: false
        };

        $scope.scrollbarVolume = {
            config: {
                autoHideScrollbar: false,
                advanced: {
                    updateOnContentResize: true
                },
                setHeight: $('#panel-product-parameters').height(),
                scrollInertia: 0
            },
            update: null
        };

        var emptyProducts = 0;
        var countGroups = 0;
        $scope.emptyProduct = false;
        $scope.selectedTechnology = false;
        $scope.quotationSend = false;

        function init() {
            $scope.productAddresses[0] = {
                ID: 1,
                deliveryID: 0,
                index: 0,
                price: 0,
                volume: 1,
                weight: 0
            };
            $(':not(.select-product-form)').on('click', function () {
                if ($scope.currentType.names !== undefined) {
                    $('#changeProductInput').attr('placeholder', $scope.currentType.names[$rootScope.currentLang.code]);
                }
            });
        }

        init();

        function loadData() {
            var def = $q.defer();

            var sequences = [];

            sequences.push(getType('', $scope.currentTypeUrl));
            sequences.push(getDeliveries());
            sequences.push(getAddress().then(function (data) {
                setAddress(data);
            }));

            if ($stateParams.categoryurl) {
                sequences.push(getCategory($stateParams.categoryurl));
            }

            $q.all(sequences).then(
                function (results) {
                    def.resolve(results);
                },
                function (errors) {
                    def.reject(errors);
                },
                function (updates) {
                    def.update(updates);
                });

            return def.promise;
        }

        var Setting = new SettingService('additionalSettings');
        Setting.getPublicSettings().then(function (settingsData) {
            $scope.alternativesAttrID = settingsData.filteredAttribute.value;
            $scope.calcWithoutDelivery = settingsData.calcWithoutDelivery.value;
        });

        function getDescriptions() {

            var SettingView = new SettingService('general');

            var groupID = $scope.currentGroupID;
            var typeID = $scope.currentTypeID;

            SettingView.getPublicSettings().then(function (settingsData) {
                PsTypeDescriptionService.getAll(groupID, typeID).then(function (data) {

                    var sliderData = [];

                    if (!_.isEmpty(data)) {

                        _.each(data, function (oneDesc) {

                            /**
                             * @param {Object} oneDesc
                             * @param {number} oneDesc.descType
                             *
                             */
                            switch (oneDesc.descType) {
                                case 1:
                                    if (settingsData.numberOfLinesInDescription &&
                                        settingsData.numberOfLinesInDescription.value > 0) {
                                        var word = '';
                                        if (oneDesc.langs[$rootScope.currentLang.code] !== undefined) {
                                            word = TextWidgetService.findWord(
                                                oneDesc.langs[$rootScope.currentLang.code].description,
                                                settingsData.numberOfLinesInDescription.value
                                            );

                                            var paragraphNumber = TextWidgetService.findParagraph(
                                                oneDesc.langs[$rootScope.currentLang.code].description,
                                                word
                                            );

                                            if (paragraphNumber !== false) {
                                                oneDesc.showLess = TextWidgetService.getLess(
                                                    oneDesc.langs[$rootScope.currentLang.code].description,
                                                    paragraphNumber
                                                );
                                                oneDesc.initHide = true;
                                            } else {

                                                var firstMatch = -1;
                                                if (oneDesc.langs[$rootScope.currentLang.code].description !== null) {
                                                    var withNoBreaks = oneDesc.langs[$rootScope.currentLang.code].description.replace(/(\r\n|\n|\r|\<br\>|\<br \/\>)/gm, "");
                                                    firstMatch = withNoBreaks.indexOf(word);
                                                }

                                                if (firstMatch > -1) {
                                                    var finalCut = firstMatch + word.length;
                                                    oneDesc.showLess = oneDesc.langs[$rootScope.currentLang.code].description.slice(0, finalCut) +
                                                        '...</p>';
                                                    oneDesc.initHide = true;
                                                } else {
                                                    oneDesc.showLess = false;
                                                }
                                            }
                                        }
                                    }

                                    if (oneDesc.langs[$rootScope.currentLang.code].description) {
                                        oneDesc.langs[$rootScope.currentLang.code].description = $sce.trustAsHtml(
                                            oneDesc.langs[$rootScope.currentLang.code].description
                                        );
                                    }

                                    if (oneDesc.showLess) {
                                        oneDesc.showLess = $sce.trustAsHtml(oneDesc.showLess);
                                    }

                                    if (oneDesc.showLess && oneDesc.visible === 1) {
                                        oneDesc.initHide = false;
                                    }

                                    $scope.descriptions.push(oneDesc);
                                    break;
                                case 5:

                                    oneDesc.items = [];

                                    if (!_.isEmpty(oneDesc.files)) {
                                        _.each(oneDesc.files, function (oneFile) {

                                            /**
                                             * @param {Object} oneFile
                                             * @param {string} oneFile.urlCrop
                                             * @param {number} oneFile.fileID
                                             */

                                            oneDesc.items.push({
                                                thumb: oneFile.urlCrop,
                                                img: oneFile.url,
                                                description: 'Image ' + oneFile.fileID
                                            });
                                        });
                                    }

                                    $scope.galleries.push(oneDesc);

                                    break;
                                case 3:

                                    sliderData.push(oneDesc);

                                    break;

                                case 6:

                                    $scope.thumbnails.push(oneDesc);

                                    break;

                                case 7:
                                    $scope.patterns = oneDesc.patterns;

                                    break;
                                case 8:
                                    $scope.seoDescription = oneDesc.langs[$rootScope.currentLang.code].description ?? '';

                                    break;
                            }

                        });


                    }

                    $rootScope.$emit('Slider:data', sliderData);

                });
            });

        }

        var selectType = function (type) {

            $scope.currentType = type;

            if ($rootScope.currentLang && $rootScope.currentLang.code && type.names) {
                $rootScope.customBreadcrumbs.calculate = type.names[$rootScope.currentLang.code];
            } else {
                $rootScope.customBreadcrumbs.calculate = $filter('translate')('product');
            }

            var promises = [];

            /**
             * @param {Object} type
             * @param {number} type.complex
             */

            if (!!type.complex) {

                $scope.complexID = type.ID;

                // complex product
                ComplexService.getAllPublic().then(function (data) {
                    countProducts = data.length;
                    var cgIndex = 0;
                    _.each(data, function (item) {
                        cgIndex++;
                        promises.push($scope.getComplexGroup(item, cgIndex));

                    });

                });

            } else {

                // normal product
                countProducts = 1;

                var group = {
                    ID: null,
                    name: type.name,
                    names: type.names,
                    productID: type.ID,
                    type: "other",
                    products: []
                };
                // if not complex type
                var product = {
                    groupID: type.groupID,
                    typeID: type.ID,
                    typeName: type.name,
                    typeNames: type.names
                };
                group.products.push(product);
                promises.push($scope.getComplexGroup(group, 1));

            }
            $q.all(promises).then(function (data) {

                getFormat();

                log.info('100% - loaded');
                updateLinkToCopy();
                setupClipboardJS();
                DomWidgetService.pinElementWhenScroll(
                    ".panel-summary",
                    ".panel-summary .panel-heading",
                    ".panel-configuration"
                );
            }, function (data) {
                console.error('ERR: Problem with products load', data);
            });

        };

        function getType(groupUrl, typeUrl) {

            PsTypeService.getOneForView(groupUrl, typeUrl).then(function (data) {
                if (data && data.active === 0) {
                    Notification.error($filter('translate')('product_currently_not_available'));
                    $state.go('home');
                    return;
                }
                $scope.currentGroupID = data.groupID;
                $scope.currentTypeID = data.ID;
                MainWidgetService.includeTemplateVariables($scope, 'calc', $scope.currentGroupID, $scope.currentTypeID);
                $scope.type = data;
                //log type

                if ($rootScope.logged === false) {
                    $scope.calcFilesSetID = localStorageService.get('calcFilesSetID');
                    if (!$scope.calcFilesSetID) {
                        CalcFileService.createGuestSet($scope.type.ID).then(function (createGuestSetResponse) {
                            $scope.calcFilesSetID = createGuestSetResponse.response ? createGuestSetResponse.calcFileSetID : null;
                            localStorageService.set('calcFilesSetID', $scope.calcFilesSetID);
                        });
                    } else {
                        CalcFileService.getBySetID($scope.calcFilesSetID).then(function (caclFilesData) {
                            $scope.calcFiles = caclFilesData;
                            $scope.setPagination($scope.calcFilesCurrentPage);
                        });
                    }
                } else {
                    CalcFileService.getAllByType($scope.type.ID).then(function (caclFilesData) {
                        $scope.calcFiles = caclFilesData;
                        $scope.setPagination($scope.calcFilesCurrentPage);
                        if (caclFilesData.length > 0) {
                            $scope.calcFilesSetID = caclFilesData[0].calcFilesSetID;
                        }
                    });
                }


                if ($rootScope.currentLang && $rootScope.currentLang.code && $rootScope.customBreadcrumbs.group === undefined) {
                    $rootScope.customBreadcrumbs.group = data.group.slugs[$rootScope.currentLang.code];
                }

                if ($rootScope.customBreadcrumbs.group === undefined) {
                    $rootScope.customBreadcrumbs.group = $filter('translate')('group');
                }

                getDescriptions();

                if ($stateParams.categoryurl === undefined && $scope.currentTypeID) {
                    getFirstCategory($scope.currentTypeID);
                }

                ComplexService = new PsComplexService(data.groupID, data.ID);

                var getTaxes = function () {

                    var def = $q.defer();
                    TaxService.getForProduct($scope.currentGroupID, $scope.currentTypeID).then(function (data) {
                        def.resolve(data);
                    });
                    return def.promise;
                };

                getTaxes().then(function (data) {
                    $scope.taxes = data;
                    if (data.length > 1) {
                        _.each($scope.taxes, function (tax) {
                            if (tax.default) {
                                $scope.productItem.taxID = tax.ID;
                            }
                        });
                    } else if (data.length === 1) {
                        $scope.productItem.taxID = $scope.taxes[0].ID;
                    }


                });

                selectType(data);

            }, function (data) {
                console.error(data);
                Notification.error($filter('translate')('error'));
            });

        }

        $scope.getComplexGroup = function (group, index) {

            var def = $q.defer();

            if (group.products.length > 0) {
                countGroups++;
            }

            $scope.complexProducts.push(group);
            var fakeTarget = [{}];
            setFromCalculationUrl(fakeTarget, 'selectedProduct', 'selectedProduct[]', null, parseInt);
            var product = fakeTarget[index-1] && fakeTarget[index-1].selectedProduct ? _.findWhere(group.products, {ID: fakeTarget[index-1].selectedProduct}) : group.products[0];
            if (!group.selectedProduct) {


                /**
                 * @param {Object} $scope.currentCalc
                 * @param {Array} $scope.currentCalc.calcProducts
                 */
                if ($scope.currentCalc) {
                    var idx = _.findIndex($scope.currentCalc.calcProducts, {typeID: product.typeID});
                    if (idx === -1) {
                        return true;
                    }
                }
                $scope.selectComplexProductSync(group, product).then(function (data) {
                    log.info('Another product loaded!')
                    timeouts.push($timeout(function () {
                        $rootScope.$emit('stopPreLoader', true);
                        $scope.selectFormatSync(group.selectedProduct.data, group.selectedProduct.data.currentFormat).then(function () {
                            if (countProducts === index) {
                                productsLoaded = true;
                                if (getCalculationUrlParam('customVolumes')) {
                                    var customVolumes = angular.fromJson(getCalculationUrlParam('customVolumes'));
                                    if (angular.isDefined(customVolumes[$scope.currentTypeID])) {
                                        $scope.customVolume = customVolumes[$scope.currentTypeID];
                                    }
                                }
                                $scope.getVolumes($scope.productItem.amount);
                                setFromCalculationUrl($scope.productItem, 'name', 'name');
                                setFromCalculationUrl($scope.productItem, 'selectedTechnologyID', 'technologyID', null, parseInt);
                                setFromCalculationUrl($scope.productItem, 'realisationTime', 'realisationTime', null, parseInt)
                                setFromCalculationUrl($scope.productItem, 'taxID', 'tax', null, parseInt)
                                setFromCalculationUrl($scope.complexProducts, 'selectedProduct.data.currentFormat.customWidth', 'customWidth[]', 'customWidth', parseInt);
                                setFromCalculationUrl($scope.complexProducts, 'selectedProduct.data.currentFormat.customHeight', 'customHeight[]', 'customHeight', parseInt);

                                var changes = setFromCalculationUrl($scope.complexProducts, 'selectedProduct.data.selectedOptions', 'attrID[]', null, parseInt);

                                _.each(changes, function (data) {
                                    _.each($scope.complexProducts[data[1]].selectedProduct.data.attributes, (attribute) => {
                                        if (attribute.attrID == data[2]) {
                                            _.each(attribute.options, (option) => {
                                                if (option.ID == data[3]) {
                                                    $scope.selectOption($scope.complexProducts[data[1]].selectedProduct.data, data[2], option)
                                                }
                                            })
                                        }
                                    });
                                });

                                setFromCalculationUrl($scope.complexProducts, 'selectedProduct.data.attrPages', 'attrPages[]', null, parseInt);
                                setFromCalculationUrl($scope.complexProducts, 'selectedProduct.data.currentPages', 'pages[]', null, parseInt);
                                setFromCalculationUrl($scope.productAddresses[0], 'deliveryID', 'deliveryID', null, parseInt);
                                $scope.getVolumes($scope.productItem.amount);
                                if (choosenPaperID) {
                                    console.log('choosenPaperID');
                                    console.log(choosenPaperID);
                                    var obj = $scope.complexProducts[0].selectedProduct.data;
                                    var allAttributes = Object.keys(obj).filter((key) => key === 'attributes').reduce((cur, key) => {
                                        return Object.assign(cur, {[key]: obj[key]})
                                    }, {});
                                    var gramsPaperAttr = allAttributes.attributes.find(function (object) {
                                        if (object.attrID === 2) return object;
                                    });
                                    var gramsPaperAllOptions = gramsPaperAttr.options;

                                    var foundPaperGramme = gramsPaperAllOptions.find(function (object) {
                                        if (object.ID === parseInt(choosenPaperID)) return object;
                                    });

                                    var foundPaperName = false,
                                        foundPaperType = false,
                                        foundPaperFamily = false;

                                    // find paper name by exclusions
                                    var namePaperAttr = allAttributes.attributes.find(function (object) {
                                        if (object.attrID === 105) return object;
                                    });
                                    console.log('namePaperAttr');
                                    console.log(namePaperAttr);
                                    var namePaperAllOptions = namePaperAttr.options;
                                    _.each(namePaperAllOptions, function (singlePaper) {
                                        if (!singlePaper.exclusions[2].includes(parseInt(choosenPaperID))) {
                                            foundPaperName = singlePaper;
                                        }
                                    });

                                    // find paper type by exclusions
                                    var typePaperAttr = allAttributes.attributes.find(function (object) {
                                        if (object.attrID === 103) return object;
                                    });
                                    var typePaperAllOptions = typePaperAttr.options;
                                    _.each(typePaperAllOptions, function (singlePaper) {
                                        if (!singlePaper.exclusions[105].includes(foundPaperName.ID)) {
                                            foundPaperType = singlePaper;
                                        }
                                    });

                                    // find paper family by exclusions
                                    var familyPaperAttr = allAttributes.attributes.find(function (object) {
                                        if (object.attrID === 55) return object;
                                    });
                                    var familyPaperAllOptions = familyPaperAttr.options;
                                    _.each(familyPaperAllOptions, function (singlePaper) {
                                        if (!singlePaper.exclusions[103].includes(foundPaperType.ID)) {
                                            foundPaperFamily = singlePaper;
                                        }
                                    });

                                    $scope.selectOption($scope.complexProducts[0].selectedProduct.data, 55, foundPaperFamily);
                                    $scope.selectOption($scope.complexProducts[0].selectedProduct.data, 103, foundPaperType);
                                    $scope.selectOption($scope.complexProducts[0].selectedProduct.data, 105, foundPaperName);
                                    $scope.selectOption($scope.complexProducts[0].selectedProduct.data, 2, foundPaperGramme);

                                }

                            }
                            def.resolve(data);
                        }, function (errorData) {
                            console.log('selectFormatSyncReject', errorData);
                            console.log(group);
                        });
                    }, 100));
                }, function (data) {
                    console.error('selectComplexProductError');
                    def.reject(data);
                });
            }

            return def.promise;

        };

        $scope.selectComplexProductSync = function (complexProduct, selectedProduct) {

            var def = $q.defer();
            complexProduct.selectedProduct = selectedProduct;

            $scope.getProduct(selectedProduct).then(function (data) {
                def.resolve(data);
            }, function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        $scope.selectComplexProduct = function (complexProduct, selectedProduct) {
            updateCalculationUrl('selectedProduct', selectedProduct.ID, null, productIndex(complexProduct));
            var def = $q.defer();
            complexProduct.selectedProduct = selectedProduct;
            $scope.getProduct(selectedProduct).then(function (data) {
                def.resolve(data);
                $scope.getVolumes($scope.productItem.amount);
            }, function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        $scope.selectDefaultOptions = function (product) {
            // product.attributes[2]=
            var currentCalcProduct = getCurrentCalcProduct(product.info);

            _.each(product.attributes, function (item) {

                if (!product.selectedOptions[item.attrID]) {
                    var currentCalcAttr = null;
                    if (currentCalcProduct) {
                        currentCalcAttr = _.find(currentCalcProduct.attributes, {attrID: item.attrID});
                    }

                    var tmp;
                    _.each(item.options, function (option) {
                        if (currentCalcAttr) {
                            if (currentCalcAttr.optID !== option.ID) {
                                return true;
                            }
                            if (currentCalcAttr.attrPages) {
                                product.attrPages[item.attrID] = currentCalcAttr.attrPages
                            }
                        }

                        if (!_.includes(product.excludedOptions, option.ID)) {
                            tmp = option;
                            return false;
                        }
                    });

                    var defaultOption = _.find(item.options, {default: 1});

                    if (defaultOption && !_.includes(product.excludedOptions, defaultOption.ID)) {
                        tmp = defaultOption;
                    }

                    $scope.selectOption(product, item.attrID, tmp);

                }
            });

        };

        function getCurrentCalcProduct(product) {
            var currentCalcProduct = null;
            if ($scope.currentCalc) {
                currentCalcProduct = _.find($scope.currentCalc.calcProducts, {typeID: product.typeID});
            }
            return currentCalcProduct;
        }

        $scope.getProduct = function (product) {

            var def = $q.defer();

            emptyProducts = 0;

            var newProduct = {
                info: product,
                selectedOptions: {},
                attrPages: {},
                attributes: {},
                attributeMap: [],
                optionMap: {},
                currentFormat: false,
                currentPages: false,
                excludedOptions: [],
                excludedByAttribute: {},
                formatExcluded: [],
                thickness: {
                    values: {},
                    min: null,
                    max: null,
                    current: null
                }
            };

            product.data = newProduct;

            AttributeService = new PsAttributeService(product.groupID, product.typeID);
            FormatService = new PsFormatService(product.groupID, product.typeID);
            PagesService = new PsPageService(product.groupID, product.typeID);

            $q.all([
                FormatService.getPublic($scope.complexID),
                PagesService.getPublic(),
                AttributeService.getFullOptions()
            ]).then(function (data) {

                newProduct.formats = data[0];

                var attributesData = data[2];

                if (attributesData.length === 0) {
                    emptyProducts++;
                }

                if (emptyProducts === countGroups) {
                    $scope.emptyProduct = true;
                }

                var customFormatIndex = _.findIndex(attributesData, {attrID: -1});
                if (customFormatIndex > -1) {
                    newProduct.customFormatInfo = attributesData[customFormatIndex];
                    attributesData.splice(1, customFormatIndex);
                }

                var customPageIndex = _.findIndex(attributesData, {attrID: -2});
                if (customPageIndex > -1) {
                    newProduct.customPageInfo = attributesData[customPageIndex];
                    attributesData.splice(1, customPageIndex);
                }

                newProduct.attributes = attributesData;

                _.each(newProduct.attributes, function (attr) {
                    newProduct.attributeMap.push(attr.attrID);
                    newProduct.optionMap[attr.attrID] = [];
                    _.each(attr.options, function (opt) {
                        newProduct.optionMap[attr.attrID].push(opt.ID);
                    });
                });

                newProduct.pages = data[1];

                newProduct.relatedFormats = _.clone(newProduct.formats);

                var currentCalcProduct = getCurrentCalcProduct(product.info);

                var formatIdx = 0;
                if (currentCalcProduct) {
                    formatIdx = _.findIndex(newProduct.relatedFormats, {ID: currentCalcProduct.formatID});
                    if (formatIdx === -1) {
                        console.error('Can\'t find format like in select calculation.');
                        return true;
                    }
                }


                $scope.selectFormatSync(newProduct, newProduct.relatedFormats[formatIdx]).then(function () {

                    if (currentCalcProduct) {
                        $scope.selectPagesSync(newProduct, currentCalcProduct.pages);
                    } else {
                        if (newProduct.pages.length && newProduct.pages[0].pages) {
                            $scope.selectPagesSync(newProduct, newProduct.pages[0].pages);
                        }
                        if (newProduct.pages.length && newProduct.pages[0].minPages) {
                            $scope.selectPagesSync(newProduct, newProduct.pages[0].minPages);
                        }
                    }
                    def.resolve(data);
                });
                for (var i = 0; i < $scope.complexProducts.length; i++) {
                    var formatFromUrl = _.find($scope.complexProducts[i].selectedProduct.data.formats, function (item) {
                        return item.ID == getCalculationUrlParam('formatID.' + i)
                    });
                    setFromCalculationUrl($scope.complexProducts[i].selectedProduct.data, 'currentFormat', 'format', formatFromUrl);
                    if($scope.complexProducts[i].selectedProduct.data.currentFormat){
                        $scope.selectFormat($scope.complexProducts[i], $scope.complexProducts[i].selectedProduct.data.currentFormat)
                    }
                }
            }, function (data) {
                def.reject(data);
                Notification.error($filter('translate')('data_retrieve_failed'));
            });

            return def.promise;
        };

        function getAttributeFromOption(product, optionID) {

            var def = $q.defer();

            _.each(product.optionMap, function (options, attrID) {
                if (_.includes(options, optionID)) {
                    def.resolve(parseInt(attrID));
                }
            });

            return def.promise;
        }

        $scope.selectFormat = function (product, format) {
            updateCalculationUrl('formatID', format.ID, null, productIndex(product));
            product.currentFormat = format;
            if (!!format.custom) {
                product.currentFormat.customWidth = format.minWidth - format.slope * 2;
                product.currentFormat.customHeight = format.minHeight - format.slope * 2;
            }

            $scope.checkRelatedFormats(product, format);

            $scope.filterRelatedFormats();

            $scope.selectDefaultFormats().then(function () {


                CalcSimplifyWidgetService.checkFormatExclusions(product, format).then(function () {

                    setExclusionsAsync(product).then(function (exclusionEnd) {

                        if (exclusionEnd) {

                            descriptionTabResetActive();

                            $scope.selectDefaultOptions(product);
                            $scope.getVolumes($scope.productItem.amount);
                        }
                    }, function (msg) {
                        console.error(msg)
                    });

                }, function (msg) {
                    console.error(msg)
                });

            }, function (data) {
                console.log(data);
            });

        };

        $scope.selectFormatSync = function (product, format) {

            var def = $q.defer();

            if (format === null || format === undefined) {
                def.reject(false);
                return def.promise;
            }

            product.currentFormat = format;
            if (format && !!format.custom) {
                product.currentFormat.customWidth = format.minWidth - format.slope * 2;
                product.currentFormat.customHeight = format.minHeight - format.slope * 2;
            }

            $scope.checkRelatedFormats(product, format);
            $scope.filterRelatedFormats();

            $scope.selectDefaultFormats().then(function () {

                CalcSimplifyWidgetService.checkFormatExclusions(product, format).then(function () {

                    setExclusionsAsync(product).then(function (exclusionEnd) {
                        if (exclusionEnd) {
                            descriptionTabResetActive();

                            $scope.selectDefaultOptions(product);

                            product.info.noCalculate = false;
                            def.resolve();
                        } else {
                            product.info.noCalculate = true;
                            def.resolve();
                        }
                    });

                });

            }, function (data) {
                console.log(data);
            });

            return def.promise;
        };

        function setExclusionsAsync(product) {

            var def = $q.defer();

            product.excludedOptions = _.clone(product.formatExcluded);
            product.excludedByAttribute = {};

            _.each(product.attributes, function (attribute) {
                attribute.filteredOptions = _.clone(attribute.options, true);
            });

            var optID = {};
            var activeAttrID;
            _.each(product.attributeMap, function (attrID) {

                activeAttrID = attrID;
                optID = product.selectedOptions[attrID];

                if (optID) {
                    var item = {};

                    if (_.isObject(optID)) {
                        item = optID;
                    } else {
                        item = getOption(product, optID);
                    }
                    if (!item) {
                        def.reject('no item for optID ' + optID);
                        return def.promise;
                    }
                    var tmpExclusions = {};

                    function printExcl(all, label) {
                        _.each(all, function (item, i) {
                            if (item.length)
                                console.log('excluded ' + label, item)
                        })
                    }

                    var exclusionsThickness = $scope.filterByThickness(product);
                    printExcl(exclusionsThickness, 'exclusionsThickness')
                    var exclusionsThicknessPages = $scope.filterByOptionsPages(product);
                    printExcl(exclusionsThicknessPages, 'exclusionsThicknessPages')

                    /**
                     * @param {Object} item
                     * @param {Array} item.exclusions
                     */
                    if (item.exclusions) {
                        tmpExclusions = _.merge({}, item.exclusions, exclusionsThickness, exclusionsThicknessPages);
                    }

                    product.excludedByAttribute[activeAttrID] = _.merge({}, item.exclusions);

                    setOptionExclusionsAsync(product, activeAttrID, tmpExclusions).then(function (isEnd) {
                        if (isEnd) {

                            checkAttrSelectAsync(product).then(function (isAttrSelectEnd) {
                                if (isAttrSelectEnd) {
                                    if (_.last(product.attributeMap) === activeAttrID) {

                                        var attrIndex = _.findIndex(product.attributes, {'attrID': attrID});

                                        if (attrIndex > -1) {
                                            if (product.attributes[attrIndex].filteredOptions.length !==
                                                $('#select-attribute-' + attrID + " option").length) {
                                                product.attributes[attrIndex].filteredOptions = angular.copy(
                                                    product.attributes[attrIndex].filteredOptions
                                                );
                                            }
                                        }

                                        def.resolve(true);
                                    }
                                } else {
                                    if (_.last(product.attributeMap) === activeAttrID) {
                                        def.resolve(true);
                                    }
                                }
                            });
                        } else {
                            if (_.last(product.attributeMap) === activeAttrID) {
                                def.resolve(true);
                            }
                        }
                    });

                } else {
                    if (_.last(product.attributeMap) === activeAttrID) {
                        def.resolve(true);
                    }
                }
            });

            if (product.attributeMap.length === 0) {
                def.resolve(false);
            }

            return def.promise;

        }

        function setOptionExclusionsAsync(product, attrID, exclusions) {

            var def = $q.defer();

            var attribute = _.find(product.attributes, {attrID: attrID});

            addExcludesFromFormatAndPages(product, exclusions).then(function () {

                addExcludedOptions(product, attribute).then(function () {

                    attribute.filteredOptions = _.filter(attribute.options, function (opt) {
                        return !_.includes(product.excludedOptions, opt.ID);
                    });

                    var selectedOption = _.find(attribute.filteredOptions, {ID: product.selectedOptions[attribute.attrID]});

                    if (selectedOption === undefined) {
                        if (attribute.filteredOptions.length > 0) {

                            var oldSelectedOptionID = product.selectedOptions[attribute.attrID];

                            var oldOptionIndex = _.findIndex(attribute.options, {ID: oldSelectedOptionID});

                            if (oldOptionIndex > -1) {
                                var flatExclusions = _.reduceRight(attribute.options[oldOptionIndex].exclusions, function (a, b) {
                                    return a.concat(b);
                                }, []);
                                product.excludedOptions = product.excludedOptions.filter(function (item) {
                                    return !flatExclusions.includes(item);
                                });
                            }

                            var flatNewExclusions = _.reduceRight(attribute.filteredOptions[0].exclusions, function (a, b) {
                                return a.concat(b);
                            }, []);

                            _.each(flatNewExclusions, function (oneOptionID) {
                                if (!_.includes(product.excludedOptions, oneOptionID)) {
                                    product.excludedOptions.push(oneOptionID);
                                }
                            });

                            product.selectedOptions[attribute.attrID] = attribute.filteredOptions[0].ID;

                            CalcSimplifyWidgetService.removeUnActiveOptions(product).then(function (removedStatus) {
                                setExclusionsAsync(product).then(function (exclusionEnd) {
                                    def.resolve(true);
                                });
                            });

                        } else {
                            console.log('Wykluczamy opcje dla atrybutu: ', attribute.attrName, product.selectedOptions[attribute.attrID]);
                            delete product.selectedOptions[attribute.attrID];
                            def.resolve(true);
                        }
                    } else {
                        def.resolve(true);
                    }

                });

            });

            return def.promise;
        }

        function addExcludesFromFormatAndPages(product, exclusions) {
            var def = $q.defer();

            var sizeOutside = _.size(exclusions);
            var iteratorOutside = 0;
            var iteratorInside;
            var sizeInside;

            if (_.size(exclusions) > 0) {
                _.each(exclusions, function (exc) {

                    sizeInside = exc.length;
                    iteratorInside = 0;

                    if (sizeInside > 0) {
                        _.each(exc, function (optID) {
                            product.excludedOptions.push(optID);

                            if (iteratorOutside === (sizeOutside - 1) && (sizeInside - 1) === iteratorInside) {
                                def.resolve(true);
                            }

                            iteratorInside++;

                        });
                    } else {

                        if (iteratorOutside === (sizeOutside - 1)) {
                            def.resolve(true);
                        }

                    }


                    iteratorOutside++;
                });
            } else {
                def.resolve(true);
            }

            return def.promise;
        }

        function aggregateSelectedOptions(product) {
            var def = $q.defer();

            var aggregateSelectedOptions = [];

            var counter = 0;
            var size = _.size(product.selectedOptions);

            _.each(product.selectedOptions, function (selectedOptID) {
                aggregateSelectedOptions.push(selectedOptID);

                if (counter === (size - 1)) {
                    def.resolve(aggregateSelectedOptions);
                }

                counter++;
            });

            return def.promise;
        }

        function addExcludedOptions(product, attribute) {
            var def = $q.defer();

            aggregateSelectedOptions(product).then(function (aggregateSelectedOptions) {

                deletedAttrs = [];

                var counter = 0;
                var size = _.size(attribute.options);

                _.each(attribute.options, function (option) {


                    if (_.size(_.intersection(aggregateSelectedOptions, option.excludesOptions)) > 0) {

                        if (_.indexOf(Object.values(product.excludedOptions), option.ID) === -1) {
                            product.excludedOptions.push(option.ID);
                        }

                        if (counter === (size - 1)) {
                            def.resolve(true);
                        }

                    } else {

                        if (counter === (size - 1)) {
                            def.resolve(true);
                        }

                    }

                    counter++;
                });

            });

            return def.promise;
        }

        function checkAttrSelectAsync(product) {
            var def = $q.defer();

            var firstFilteredOption = null;

            _.each(product.attributes, function (attribute) {

                if (_.includes(deletedAttrs, attribute.attrID)) {
                    if (product.selectedOptions[attribute.attrID]) {
                        firstFilteredOption = _.first(attribute.filteredOptions);
                        if (firstFilteredOption) {
                            product.selectedOptions[attribute.attrID] = firstFilteredOption.ID;
                        }
                    } else {

                        attribute.filteredOptions = _.filter(attribute.options, function (opt) {
                            return !_.includes(product.excludedOptions, opt.ID);
                        });

                        firstFilteredOption = _.first(attribute.filteredOptions);

                        if (firstFilteredOption) {

                            var flat = _.reduceRight(firstFilteredOption.exclusions, function (a, b) {
                                return a.concat(b);
                            }, []);
                            product.excludedOptions = _.merge({}, product.excludedOptions, flat);

                            product.selectedOptions[attribute.attrID] = firstFilteredOption.ID;
                        }

                    }
                }

                if (_.last(product.attributeMap) === attribute.attrID) {
                    def.resolve(true);
                }

            });

            return def.promise;
        }

        $scope.checkRelatedFormats = function (product, format) {

            if (!format.relatedFormats) {
                return true;
            }
            $scope.relatedFormats = [];
            _.each(format.relatedFormats, function (item) {
                $scope.relatedFormats.push({ID: item.formatID, typeID: item.typeID});
            });

        };

        $scope.filterRelatedFormats = function () {

            _.each($scope.complexProducts.slice(1), function (oneProduct) {
                if (oneProduct.selectedProduct) {
                    if ($scope.complexProducts[0].selectedProduct.data.formats.length === 1) {
                        oneProduct.selectedProduct.data.relatedFormats = _.clone(oneProduct.selectedProduct.data.formats);
                    } else {
                        oneProduct.selectedProduct.data.relatedFormats = filterFormats(oneProduct.selectedProduct.data.formats, $scope.relatedFormats);
                    }

                }
            });

        };

        function filterFormats(input, ids) {

            var result = [];

            _.each(input, function (item) {
                var idx = _.findIndex(ids, {ID: item.ID});
                if (idx > -1) {
                    result.push(item);
                }
            });
            return result;

        }

        $scope.selectDefaultFormats = function () {

            var def = $q.defer();
            var formatChange = false;

            _.each($scope.complexProducts.slice(1), function (oneProduct) {

                if (!oneProduct.selectedProduct) {
                    return true;
                }


                var product = oneProduct.selectedProduct.data;

                var currentFormat = product.currentFormat;

                var find = -1;
                if (!!currentFormat) {
                    find = _.findIndex($scope.relatedFormats, {ID: currentFormat.ID, typeID: product.info.typeID});
                }

                if (find === -1) {

                    if (!angular.isDefined(product.relatedFormats) || product.relatedFormats.length === 0) {
                        product.currentFormat = null;
                        return true;
                    } else {
                        var searchFormat = filterFormats(product.formats, $scope.relatedFormats)[0];

                        if (searchFormat) {
                            product.currentFormat = searchFormat;
                            if (!!searchFormat.custom) {
                                product.currentFormat.customWidth = searchFormat.minWidth - searchFormat.slope * 2;
                                product.currentFormat.customHeight = searchFormat.minHeight - searchFormat.slope * 2;
                            }
                        }
                    }

                    if (!product.currentFormat) {
                        def.reject({'info': 'select another format'});
                        Notification.error($filter('translate')('not_related_format_for_product') + ' - ' + product.info.typeName);
                    }

                } else {
                    var idx = _.findIndex(product.relatedFormats, {ID: currentFormat.ID});
                    if (idx > -1) {
                        product.currentFormat = product.relatedFormats[idx];
                    }
                }

                CalcSimplifyWidgetService.checkFormatExclusions(product).then(function () {

                    setExclusionsAsync(product).then(function (exclusionEnd) {

                        if (exclusionEnd) {
                            $scope.selectDefaultOptions(product);
                        }
                    });

                });

            });

            if (!formatChange) {
                def.resolve();
            } else {
                console.log('Format change error!');
            }

            return def.promise;
        };
        function getGroup(currentGroupUrl) {

            PsGroupService.getOneForView(currentGroupUrl).then(function (data) {
                $scope.group = data;
                if ($rootScope.currentLang && $rootScope.currentLang.code) {
                    $rootScope.customBreadcrumbs.group = data.names[$rootScope.currentLang.code];
                } else {
                    $rootScope.customBreadcrumbs.group = $filter('translate')('group');
                }
                getType(currentGroupUrl, $scope.currentTypeUrl);
            }, function (data) {
                console.error(data);
                Notification.error($filter('translate')('error'));
            });
        }

        function getCategory(currentCategoryUrl) {
            DpCategoryService.getOneForView(currentCategoryUrl).then(function (data) {
                if ($rootScope.currentLang && $rootScope.currentLang.code && data.langs) {
                    $rootScope.customBreadcrumbs.category = data.langs[$rootScope.currentLang.code].name;
                } else {
                    $rootScope.customBreadcrumbs.category = $filter('translate')('category');
                }
            }, function (data) {
                console.error(data);
                Notification.error($filter('translate')('error'));
            });
        }

        function getFirstCategory(typeID) {
            DpCategoryService.getFirstByType(typeID).then(function (data) {
                if ($rootScope.currentLang && $rootScope.currentLang.code && data.langs) {
                    $rootScope.customBreadcrumbs.category = data.langs[$rootScope.currentLang.code].name;
                } else {
                    $rootScope.customBreadcrumbs.category = $filter('translate')('category');
                }
            }, function (data) {
                console.error(data);
            });
        }

        function getFormat() {

            FormatService = new PsFormatService($scope.currentGroupID, $scope.currentTypeID);
            FormatService.getPublic($scope.complexID).then(function (data) {

                $scope.type.formats = data;
                $scope.type.currentFormat = $scope.type.formats[0];

            }, function (data) {
                console.error('format err: ', data);
            });
        }

        $scope.selectOption = function (product, attrID, item) {

            var itemExist = true;

            if (item === undefined) {
                itemExist = false;
                var optID = product.selectedOptions[attrID];

                item = getOption(product, optID);

                if (item === undefined) {
                    return false;
                }
            }
            if(product.attributes[product.attributeMap.indexOf(parseInt(attrID))].displayImageOnMiniature){
                $scope.optionFileUrl =  item.icon ? item.icon.url : null
            }


            product.selectedOptions[attrID] = parseInt(item.ID);

            setRangePages(product, attrID);

            if (product.thickness.minAttr === attrID) {
                product.thickness.min = null;
                product.thickness.minAttr = null;
            }

            if (product.thickness.maxAttr === attrID) {
                product.thickness.max = null;
                product.thickness.maxAttr = null;
            }

            /**
             * @param {Object} item
             * @param {number|null} item.minThickness
             * @param {number|null} item.maxThickness
             * @param {number} item.sizePage
             */
            if (Number(item.minThickness) > 0 && (Number(item.minThickness) > product.thickness.min || item.minThickness === null)) {
                product.thickness.min = item.minThickness;
                product.thickness.minAttr = attrID;
            }

            if (Number(item.maxThickness) > 0 && (Number(item.maxThickness) < product.thickness.max || product.thickness.max === null)) {

                product.thickness.max = item.maxThickness;
                product.thickness.maxAttr = attrID;
            }

            product.thickness.values[attrID] = item.sizePage;

            if (product.pages.length) {
                $scope.calcProductThickness(product);
                $scope.getMinimumThickness(product);
                $scope.getMaximumThickness(product);
            }

            setExclusionsAsync(product).then(function (exclusionEnd) {
                if (exclusionEnd) {
                    $scope.selectDefaultOptions(product);
                    if (!itemExist) {
                        $scope.getVolumes($scope.productItem.amount);
                    }
                }

            });
            if (productsLoaded) {
                updateCalculationUrl('attrID', product.selectedOptions[attrID], attrID, productIndex(product));
            }
        };

        function productIndex(productOrGroup) {
            var idInItem = null;
            if (productOrGroup.selectedProduct) {
                idInItem = productOrGroup.selectedProduct.typeID
            } else if (productOrGroup.productID) {
                idInItem = productOrGroup.productID
            } else if (productOrGroup.info.typeID) {
                idInItem = productOrGroup.info.typeID
            }
            var index = _.findIndex($scope.complexProducts, function (item) {
                if (item.selectedProduct && item.selectedProduct.typeID) {
                    return item.selectedProduct.typeID == idInItem;
                }
                return item.productID == idInItem;
            });
            return index;
        }

        function excludeDeliveries() {

            $scope.filteredDeliveries = _.clone($scope.deliveries);

            var optID;

            _.each($scope.complexProducts, function (complexProduct, index) {

                var product = complexProduct.selectedProduct.data;

                _.each(product.attributeMap, function (attrID) {

                    optID = product.selectedOptions[attrID];

                    if (optID) {
                        var item = getOption(product, optID);

                        if (item && item.deliveries) {

                            _.each(item.deliveries, function (deliveryID) {

                                var deliveryIndex = _.findIndex($scope.filteredDeliveries, {ID: deliveryID});

                                if (deliveryIndex > -1) {

                                    $scope.filteredDeliveries.splice(deliveryIndex, 1);

                                    _.each($scope.productAddresses, function (productAddress, index) {

                                        if (productAddress.deliveryID === deliveryID && !_.isEmpty($scope.filteredDeliveries)) {
                                            productAddress.deliveryID = _.first($scope.filteredDeliveries).ID;
                                        }
                                    });

                                }
                            });
                        }
                    }

                });

            });

        }

        var getOption = function (product, optID) {

            var item = undefined;
            _.each(product.attributes, function (attribute) {
                var idx = _.findIndex(attribute.options, {ID: optID});

                if (idx > -1) {
                    item = attribute.options[idx];
                    return false;
                }

            });

            return item;
        };

        $scope.filterByThickness = function (product) {

            var exclusions = {};

            _.each(product.attributes, function (attribute) {

                exclusions[attribute.attrID] = [];
                var idx;
                _.each(attribute.options, function (option) {

                    if (angular.isDefined(option.maxThickness) && Number(option.maxThickness) > 0) {

                        if (product.thickness.current > option.maxThickness) {

                            idx = product.excludedOptions.indexOf(option.ID);
                            if (idx === -1) {
                                exclusions[attribute.attrID].push(option.ID);
                            }

                        }
                    }

                    if (angular.isDefined(option.minThickness) && Number(option.minThickness) > 0) {

                        if (product.thickness.current < option.minThickness) {

                            idx = product.excludedOptions.indexOf(option.ID);
                            if (idx === -1) {
                                exclusions[attribute.attrID].push(option.ID);
                            }

                        }

                    }

                });

            });

            return exclusions;
        };

        $scope.filterByOptionsPages = function (product) {

            var exclusions = {};

            _.each(product.attributes, function (attribute) {

                exclusions[attribute.attrID] = [];

                _.each(attribute.options, function (option) {

                    /**
                     * @param {number} option.maxPages
                     */

                    if (product.currentPages && angular.isDefined(option.maxPages) && Number(option.maxPages) > 0) {

                        if (product.currentPages > option.maxPages) {

                            idx = product.excludedOptions.indexOf(option.ID);
                            if (idx === -1) {
                                exclusions[attribute.attrID].push(option.ID);
                            }

                        }
                    }

                    if (product.currentPages && angular.isDefined(option.minPages) && Number(option.minPages) > 0) {

                        if (product.currentPages < option.minPages) {

                            var idx = product.excludedOptions.indexOf(option.ID);

                            if (idx === -1) {
                                exclusions[attribute.attrID].push(option.ID);
                            }

                        }

                    }

                });

            });

            return exclusions;
        };

        var setRangePages = function (product, attrID) {

            var idx = _.findIndex(product.attributes, {attrID: attrID});
            if (idx > -1) {
                if (product.attributes[idx].minPages !== null) {
                    if (!product.attrPages[attrID]) {
                        product.attrPages[attrID] = product.attributes[idx].minPages;
                    }
                }
            } else {
                console.log(`Attribute ${attrID} not found`);
            }
        };

        $scope.selectPagesSync = function (product, pages) {
            product.currentPages = pages;
            $scope.calcProductThickness(product);
        };

        $scope.selectPages = function (product, pages) {
            updateCalculationUrl('pages', pages, null, productIndex(product));
            pages = Number(pages);

            if (product.pages[0].pages) {

                product.currentPages = pages;

                $scope.calcProductThickness(product);
                setExclusionsAsync(product).then(function (exclusionEnd) {
                    if (exclusionEnd) {
                        _.each(product.attrPages, function (oneAttrPage, attrID) {
                            if (product.currentPages < oneAttrPage) {
                                product.attrPages[attrID] = product.currentPages;
                            }
                        });

                        $scope.getVolumes($scope.productItem.amount);
                    }
                });

            } else {
                if (product.pages[0].step !== null) {
                    var step = Number(product.pages[0].step);
                }

                if (angular.isDefined(stopSelect)) {
                    $timeout.cancel(stopSelect);
                    stopSelect = undefined;
                }

                stopSelect = $timeout(function () {
                    var maxPages = $scope.getMaximumThickness(product);
                    var minPages = $scope.getMinimumThickness(product);

                    if (parseInt(product.pages[0].maxPages) > 0 && maxPages > parseInt(product.pages[0].maxPages)) {
                        maxPages = parseInt(product.pages[0].maxPages);
                    }

                    if (product.pages[0].minPages !== null && minPages < parseInt(product.pages[0].minPages)) {
                        minPages = parseInt(product.pages[0].minPages);
                    }

                    if (product.pages[0].step !== null) {
                        if (pages % step !== 0) {
                            if ((pages % step) > (step / 2)) {
                                pages = pages + (step - (pages % step));
                            } else {
                                pages -= pages % step;
                            }
                        }
                    }

                    if (pages > maxPages) {
                        Notification.info($filter('translate')('maximum_number_of_pages') + ' ' + maxPages);
                        product.currentPages = maxPages;
                        pages = maxPages;
                    } else if (pages < minPages) {
                        Notification.info($filter('translate')('minimum_number_of_pages') + ' ' + minPages);
                        product.currentPages = minPages;
                        pages = minPages;
                    } else if (pages === undefined) {
                        Notification.info($filter('translate')('range_of_pages') + ' ' + minPages + ' - ' + maxPages);
                    } else {
                        product.currentPages = pages;
                    }

                    $scope.calcProductThickness(product);

                    setExclusionsAsync(product).then(function (exclusionEnd) {

                        if (exclusionEnd) {
                            _.each(product.attrPages, function (oneAttrPage, attrID) {
                                if (product.currentPages < oneAttrPage) {
                                    product.attrPages[attrID] = product.currentPages;
                                }
                            });

                            if (pages <= maxPages && pages >= minPages && pages !== undefined) {
                                $scope.getVolumes($scope.productItem.amount);
                            }
                        }

                    });

                }, 1000);
                timeouts.push(stopSelect)
            }
        };

        $scope.selectAttrPages = function (complexProduct, attrID) {
            updateCalculationUrl('attrPages', complexProduct.selectedProduct.data.attrPages[attrID], attrID, productIndex(complexProduct))
            if (angular.isDefined(stopSelectAttr)) {
                $timeout.cancel(stopSelectAttr);
                stopSelectAttr = undefined;
            }

            stopSelectAttr = $timeout(function () {

                if (complexProduct.selectedProduct.data.attrPages[attrID] <= 0) {
                    complexProduct.selectedProduct.data.attrPages[attrID] = 0;
                }

                var attrIdx = _.findIndex(complexProduct.selectedProduct.data.attributes, {attrID: parseInt(attrID)});

                if (attrIdx > -1) {
                    var attribute = complexProduct.selectedProduct.data.attributes[attrIdx];

                    var maxPages = attribute.maxPages;
                    if (maxPages === null) {
                        maxPages = complexProduct.selectedProduct.data.currentPages;
                    }

                    if (complexProduct.selectedProduct.data.attrPages[attrID] > maxPages) {
                        Notification.info($filter('translate')('maximum_number_of_pages') + ' ' + maxPages);
                        complexProduct.selectedProduct.data.attrPages[attrID] = maxPages;
                        return;
                    }

                    if (complexProduct.selectedProduct.data.attrPages[attrID] < attribute.minPages) {
                        Notification.info($filter('translate')('minimum_number_of_pages') + ' ' + attribute.minPages);
                        complexProduct.selectedProduct.data.attrPages[attrID] = attribute.minPages;
                        return;
                    }
                }


                $scope.getVolumes($scope.productItem.amount);
            }, 1500);
            timeouts.push(stopSelectAttr)
        };

        $scope.calcProductThickness = function (product) {

            var sheets = product.currentPages / 2;

            if (!_.keys(product.thickness.values).length) {
                product.thickness.current = null;
                return true;
            }
            /**
             * @param {number} product.pages[].doublePage
             */
            var doublePage = !!product.pages[0].doublePage;

            if (doublePage) {
                sheets /= 2;
            }

            var value = 0;
            var keyThickness = _.keys(product.thickness.values);
            var tmpAttrID = null;
            _.each(_.values(product.thickness.values), function (one, index) {
                tmpAttrID = keyThickness[index];
                if (Number(one) > 0 && _.has(product.selectedOptions, tmpAttrID)) {
                    value += one;
                }
            });

            product.thickness.current = sheets * value;

            $scope.summaryThickness[product.info.typeID] = product.thickness.current;

            return true;
        };

        $scope.getMinimumThickness = function (type) {

            if (!_.keys(type.thickness.values).length || !type.thickness.min) {

                var minPages = getMinPages(type);

                if (minPages > type.pages[0].minPages) {
                    return minPages;
                }

                return type.pages[0].minPages || 0;
            }

            var value = 0;
            _.each(_.values(type.thickness.values), function (one) {
                if (Number(one) > 0) {
                    value += one;
                }
            });

            var sheets = type.thickness.min / value;
            var pages = Math.ceil(sheets) * 2;
            var doublePage = !!type.pages[0].doublePage;
            if (doublePage) {
                pages *= 2;
            }

            if (!!type.pages[0].step) {
                var modulo = pages % type.pages[0].step;
                if (modulo) {
                    pages += type.pages[0].step - modulo;
                }
            }

            if (type.currentPages < pages) {
                $scope.selectPages(type, pages);
            }

            return pages;
        };

        var getMinPages = function (type) {

            /**
             * @param {Array} type.minOptionPages
             */

            if (_.size(type.minOptionPages)) {
                return _.min(_.values(type.minOptionPages));
            }

            return false;
        };

        $scope.getMaximumThickness = function (product) {

            if (!_.keys(product.thickness.values).length || !product.thickness.max) {
                return product.pages[0].maxPages || 9999999;
            }

            var value = 0;
            _.each(_.values(product.thickness.values), function (one) {
                if (Number(one) > 0) {
                    value += one;
                }
            });

            var sheets = product.thickness.max / value;
            var pages = Math.floor(sheets) * 2;
            var doublePage = !!product.pages[0].doublePage;
            if (doublePage) {
                pages *= 2;
            }

            if (!!product.pages[0].step) {
                var modulo = pages % product.pages[0].step;
                if (modulo) {
                    pages -= modulo;
                }
            }

            if (product.currentPages > pages) {
                $scope.selectPages(product, pages);
            }

            return pages;
        };

        $scope.count = function (volume) {

            if (volume === undefined) {
                volume = $scope.productItem.volume;
            }

            getPreparedProduct(volume).then(function (data) {

                CalculationService.calculate($scope.currentTypeID, $scope.currentGroupID, data).then(function (data) {

                    $scope.info = data.info;
                    $scope.calculation = data.calculation;

                }, function (data) {
                    console.error('calc err: ', data);
                });
            });

        };

        function checkForAuth() {
            var authorizedOnlyCalculation = false;
            if (!$rootScope.logged) {
                _.each($scope.complexProducts, function (cp) {
                    _.each(cp.products, function (p) {
                        if (p.data) {
                            for (var kAttr in p.data.selectedOptions) {
                                kAttr = Number(kAttr);
                                var kOpt = p.data.selectedOptions[kAttr]
                                var attrIndx = p.data.attributeMap.indexOf(kAttr)
                                var attr = p.data.attributes[attrIndx]
                                var opt = _.find(attr.options, function (op) {
                                    return op.ID == kOpt
                                });
                                authorizedOnlyCalculation = authorizedOnlyCalculation || opt.authorizedOnlyCalculation
                                if(opt.authorizedOnlyCalculation){
                                    console.log('opt.authorizedOnlyCalculation '+attr.attrID+' '+opt.ID)
                                }
                            }
                        }
                    });
                })
            }
            $scope.authorizedOnlyCalculation = authorizedOnlyCalculation;
        }

        $scope.calculate = function (amount, volume) {
            checkForAuth()
            $scope.calculation = {};

            $scope.calculationInfo = [];
            getPreparedProduct(amount, volume).then(function (preparedProduct) {

                CalculateService = new CalculationService(preparedProduct.groupID, preparedProduct.typeID);
                CalculateService.calculate(preparedProduct).then(function (data) {
                    $scope.calculationStep = 2;
                    $scope.showCalculation(data);
                    if (!$scope.productAddresses[0].deliveryID) {
                        $scope.productAddresses[0].deliveryID = $scope.deliveries[0].ID;
                        $scope.productAddresses[0].index = 0;
                        $scope.productAddresses[0].ID = 1;
                    }
                    var address = $scope.productAddresses[0];
                    address.weight = data.weight;
                    address.volume = volume;
                    address.amount = amount;
                    address.allVolume = volume * amount;

                    excludeDeliveries();

                    if ($rootScope.logged !== false) {
                        DeliveryWidgetService.getPkgWeightCalc(
                            address,
                            $scope
                        );
                    } else {
                        DeliveryWidgetService.getPkgWeightLite(
                            address,
                            DeliveryWidgetService.getVolume($scope, address),
                            $scope
                        );
                    }

                    $('#scrollbar-volume').height(
                        $('#panel-product-parameters').outerHeight() - ($('#panel-product-volumes').outerHeight() - $('.mCustomScrollbar').outerHeight())
                    );

                }, function (data) {
                    console.error(data);
                    Notification.error($filter('translate')('error'));
                });

            });


        };

        $scope.showCalculation = function (data) {

            $scope.calculation = data.calculation;

            $scope.calculationInfo = data.info;
            $scope.prepareUrl();

            if (!_.isEmpty($scope.rememberVolume)) {

                var idxRT = _.findIndex($scope.realisationTimes, {ID: $scope.rememberVolume.realisationTime.ID});
                if (idxRT !== -1) {
                    var idxVol = _.findIndex($scope.realisationTimes[idxRT].volumes, {volume: $scope.rememberVolume.volume.volume});
                    if (idxVol !== -1) {
                        $scope.checkVolume(false, $scope.rememberVolume.realisationTime, $scope.realisationTimes[idxRT].volumes[idxVol]);
                    } else {
                        $scope.checkVolume(false, $scope.realisationTimes[0], $scope.realisationTimes[0].volumes[0]);
                    }

                } else {
                    $scope.checkVolume(false, $scope.rememberVolume.realisationTime, $scope.rememberVolume.volume);
                }


            } else {
                if (getCalculationUrlParam('realisationTime')) {
                    var realisationTime = _.find($scope.realisationTimes, function (item) {
                        return item.ID == getCalculationUrlParam('realisationTime');
                    });
                } else {
                    var realisationTime = _.sortBy($scope.realisationTimes, 'order')[0];
                }

                if (getCalculationUrlParam('volume')) {
                    var volumeIdx = _.findIndex(realisationTime.volumes, function (item) {
                        return item.volume == getCalculationUrlParam('volume');
                    });
                } else {
                    var volumeIdx = 0;
                }

                if ($scope.type.allowCalcFilesUpload == 1) {
                    var volumeIdx = _.findIndex(realisationTime.volumes, function (item) {
                        return item.volume == caclulateCalcFilesVolume();
                    });
                    if (volumeIdx === -1) {
                        volumeIdx = 0;
                        $scope.isAddToCartDisabled = true;
                    }
                }
                var activeVolume = getActiveVolume(realisationTime.volumes, volumeIdx);

                $scope.checkVolume(false, realisationTime, activeVolume);
                if (getCalculationUrlParam('volume')) {
                    setFromCalculationUrl($scope.productItem, 'volume', 'volume', null, parseInt)
                } else {
                    $scope.productItem.volume = activeVolume.volume;
                }
            }
            $rootScope.$emit('calculation', $scope.calculation)
        };

        var getActiveVolume = function (volumes, index) {

            var actVolume = volumes[index];

            if (actVolume) {
                if (actVolume.active === false) {
                    return getActiveVolume(volumes, (index + 1));
                } else {
                    return actVolume;
                }
            } else {
                console.error('Problem with realization time!');
            }
        };

        function getPreparedProduct(amount, volume) {

            var def = $q.defer();

            var newItem = {};

            newItem.amount = amount;
            if (!(volume === undefined)) newItem.volume = volume;
            newItem.groupID = $scope.currentGroupID;
            newItem.typeID = $scope.currentTypeID;
            newItem.taxID = $scope.productItem.taxID;
            newItem.name = $scope.productItem.name;
            newItem.realizationTimeID = $scope.productItem.realisationTime;
            if ($scope.productItem.selectedTechnologyID) {
                newItem.selectedTechnology = _.findWhere($scope.technologies,{ID:$scope.productItem.selectedTechnologyID});
            }

            var rIdx = _.findIndex($scope.realisationTimes, {ID: $scope.productItem.realisationTime});

            if (rIdx > -1) {
                if ($scope.realisationTimes[rIdx].overwriteDate !== undefined && $scope.realisationTimes[rIdx].overwriteDate !== null) {
                    newItem.realizationDate = $scope.realisationTimes[rIdx].overwriteDate;
                } else {
                    newItem.realizationDate = $scope.realisationTimes[rIdx].date;
                }
            }

            DeliveryWidgetService.reducePostData($scope.productAddresses).then(function (productAddresses) {

                newItem.productAddresses = productAddresses;
                if ($scope.calculation !== undefined) {
                    newItem.weight = $scope.calculation.weight;
                }

                newItem.currency = $rootScope.currentCurrency.code;

                prepareProductPromise(newItem).then(function (newItemPrepared) {
                    if (newItemPrepared) {
                        def.resolve(newItemPrepared);
                    }
                });

            });

            return def.promise;

        }

        function prepareProductPromise(newItem) {

            var def = $q.defer();

            newItem.products = [];
            var cnt=0;
            _.each($scope.complexProducts, function (complexProduct, index) {

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
                    const printAttr = product.attributes.find((attr => attr.type === 2));
                    const printOptID = product.selectedOptions[printAttr?.attrID];
                    newProduct.pages = printAttr?.options.find((opt => opt.ID === printOptID)).doubleSidedSheet ? 2 : 1;
                }
                newProduct.options = [];

                CalcSimplifyWidgetService.removeEmptyOptionFromSelected(product, newProduct)

                newProduct.attrPages = product.attrPages;

                if (product.info.noCalculate !== true) {
                    newItem.products.push(newProduct);
                }

                if ($scope.complexProducts.length === ++cnt) {
                    def.resolve(newItem);
                }

            });

            return def.promise;
        }


        $scope.getVolumes = function (amount) {
            $scope.calculationStep = 0;
            $scope.loadVolumes = true;

            getPreparedProduct(amount).then(function (preparedProduct) {

                if ($scope.type.allowCalcFilesUpload == 1) {
                    var newVolume = {'volume': caclulateCalcFilesVolume(), 'active': true};
                    $scope.customVolume.volumes = [newVolume];
                }
                preparedProduct.customVolumes = $scope.customVolume.volumes;
                CalculateService = new CalculationService(preparedProduct.groupID, preparedProduct.typeID);

                CalculateService.getVolumes(preparedProduct).then(function (data) {
                    $scope.calculationStep = 1;
                    $scope.technologies=data.technologies

                    data.volumes.filter(function (element) {
                        return element.active === true;
                    });

                    $scope.showVolumes(data);

                    /**
                     * @param {Object} data.volumeInfo
                     */
                    if (angular.isDefined(data.volumeInfo)) {
                        $scope.customVolume.custom = data.volumeInfo.custom;
                        $scope.customVolume.maxVolume = data.volumeInfo.maxVolume;
                    }

                    $scope.getMinVolume();

                    getJson();

                }, function (data) {
                    console.log(data);
                    Notification.error($filter('translate')('error'));
                });
            });


        };

        $scope.showVolumes = function (data) {

            $scope.volumes = data.volumes;
            $scope.realisationTimes = data.realisationTimes;

            if ($scope.type.allowCalcFilesUpload == 1) {
                $scope.calculate($scope.productItem.amount, caclulateCalcFilesVolume());
            } else {
                if (angular.isDefined($scope.rememberVolume.volume)) {
                    $scope.calculate($scope.productItem.amount, $scope.rememberVolume.volume.volume);
                } else {
                    if (angular.isDefined($scope.volumes[0])) {
                        $scope.calculate($scope.productItem.amount, $scope.volumes[0].volume);
                    } else {
                        console.log('volumes: ', $scope.volumes);
                    }
                }
            }
        };

        $scope.countAttrNotExcludedOptions = function (product, attr) {

            var count = 0;
            _.each(attr.options, function (option) {

                if (!_.includes(product.excludedOptions, option.ID)) {
                    count++;
                }

            });
            return count;
        };

        $scope.prepareUrl = function () {

            if ($scope.complexProducts.length === 1 && $scope.calculation.amount > 0) {

                getPreparedProduct($scope.calculation.amount).then(function (preparedProduct) {
                    var product = preparedProduct.products[0];

                    /**
                     * @param {string} $config.EDITOR_URL
                     */

                    $scope.editorUrl = $config.EDITOR_URL + '?' + 'typeID=' + product.typeID + '&formatID=' + product.formatID + '&pages=' + product.pages;

                    _.each(product.options, function (opt) {
                        $scope.editorUrl += '&' + opt.attrID + '=' + opt.optID;
                    });
                });

            }
        };

        $scope.checkVolume = function (isFromClient, realisationTime, volume) {

            if ($scope.type.allowCalcFilesUpload == 1 && isFromClient) {
                Notification.error($filter('translate')('volume_calculates_automaticly_from_image_files'));
                return;
            } else {

                _.each($scope.realisationTimes, function (val) {
                    val.overwriteDate = null;
                });

                var idxRT = _.findIndex($scope.realisationTimes, {ID: realisationTime.ID});

                if (idxRT !== -1) {

                    $scope.rememberVolume.realisationTime = $scope.realisationTimes[idxRT];

                    $scope.realisationTimes[idxRT].overwriteDate = volume.date;

                    var idxV = _.findIndex($scope.realisationTimes[idxRT].volumes, {volume: volume.volume});
                    if (idxV !== -1) {
                        $scope.rememberVolume.volume = volume;

                        $scope.activeVolume.rtID = $scope.realisationTimes[idxRT].ID;
                        $scope.activeVolume.volume = $scope.calculation.volume = $scope.realisationTimes[idxRT].volumes[idxV].volume;

                        $scope.calculation.priceTotal = $scope.realisationTimes[idxRT].volumes[idxV].price;

                        /**
                         * @param {number} $scope.realisationTimes[].volumes[].priceBrutto
                         */
                        $scope.calculation.priceTotalBrutto = $scope.realisationTimes[idxRT].volumes[idxV].priceBrutto;
                        $scope.calculation.weight = $scope.realisationTimes[idxRT].volumes[idxV].weight;
                        if ($scope.realisationTimes[idxRT].overwriteDate) {
                            $scope.calculation.realisationTime = $scope.realisationTimes[idxRT].overwriteDate;
                        } else {
                            $scope.calculation.realisationTime = $scope.realisationTimes[idxRT].date;
                        }

                        _.each($scope.realisationTimes[idxRT].volumes, function (actVolume) {


                            var idxVol = _.findIndex($scope.volumes, {volume: actVolume.volume});

                            if (idxVol !== -1) {
                                $scope.volumes[idxVol].active = actVolume.active;
                            }

                        });
                        $scope.activeVolume.priceListIcons=_.find($scope.volumes,function(item){
                            return item.volume==volume.volume
                        }).calculation.priceListIcons;
                        $scope.productItem.volume = volume.volume;
                        updateCalculationUrl('volume', volume.volume);
                        _.each($scope.realisationTimes, function (realisationTime, rIndex) {
                            var idxVol = _.findIndex(realisationTime.volumes, {volume: volume.volume});
                            if (idxVol !== -1) {
                                $scope.realisationTimes[rIndex].active = realisationTime.volumes[idxVol].active;
                            }
                        });
                        $scope.productItem.realisationTime = realisationTime.ID;
                        updateCalculationUrl('realisationTime', $scope.productItem.realisationTime);
                        $scope.loadVolumes = false;
                        $scope.getTotalThickness();
                    }
                } else {
                    $scope.rememberVolume = {};
                }
            }
        };


        $scope.changeVolume = function () {

            if ($scope.type.allowCalcFilesUpload == 1) {
                Notification.error($filter('translate')('volume_calculates_automaticly_from_image_files'));
                $scope.productItem.volume = caclulateCalcFilesVolume();
                return;
            } else {
                var volume = $scope.productItem.volume;
                var idx;

                if (!_.isEmpty($scope.rememberVolume)) {

                    idx = _.findIndex($scope.rememberVolume.realisationTime.volumes, {volume: volume});

                    if (idx !== -1) {
                        $scope.checkVolume(false, $scope.rememberVolume.realisationTime, $scope.rememberVolume.realisationTime.volumes[idx]);
                    } else {
                        idx = _.findIndex($scope.realisationTimes[0].volumes, {volume: volume});
                        if (idx !== -1) {
                            $scope.checkVolume(false, $scope.realisationTimes[0], $scope.realisationTimes[0].volumes[idx]);
                        }
                    }

                } else {

                    idx = _.findIndex($scope.realisationTimes[0].volumes, {volume: volume});
                    if (idx !== -1) {
                        $scope.checkVolume(false, $scope.realisationTimes[0], $scope.realisationTimes[0].volumes[idx]);
                    }

                }
                if (typeof $scope.scrollbarVolume.update === 'function') {
                    $scope.scrollbarVolume.update("scrollTo", "#row-volume-" + $scope.productItem.volume);
                }
            }
        };

        $scope.addVolume = function () {

            if (parseInt($scope.customVolume.maxVolume) < parseInt($scope.customVolume.newVolume)) {
                $scope.customVolume.newVolume = $scope.customVolume.maxVolume;
                Notification.error($filter('translate')('to_high_volume') + ' - ' + $scope.customVolume.maxVolume);
                return;
            }

            if (parseInt($scope.customVolume.minVolume) > parseInt($scope.customVolume.newVolume)) {
                $scope.customVolume.newVolume = $scope.customVolume.minVolume;
                Notification.error($filter('translate')('to_low_volume') + ' - ' + $scope.customVolume.minVolume);
                return;
            }

            if ($scope.customVolume.newVolume === undefined) {
                $scope.customVolume.newVolume = $scope.customVolume.minVolume;
                Notification.error($filter('translate')('incorrect_volume'));
                return;
            }

            var newVolume = {'volume': $scope.customVolume.newVolume, 'active': true};
            if (!angular.isDefined($scope.customVolume.volumes)) {
                $scope.customVolume.volumes = [];
            }

            var idxV = _.findIndex($scope.volumes, {volume: $scope.customVolume.newVolume});
            var idxCV = _.findIndex($scope.customVolume.volumes, {volume: $scope.customVolume.newVolume});

            if (idxV === -1 && idxCV === -1) {

                $scope.customVolume.volumes.push(newVolume);
                $scope.rememberVolume.volume = newVolume;
                $scope.getVolumes($scope.productItem.amount);

                var cookieCustomVolumes = angular.fromJson($cookies['customVolumes']);

                if (!cookieCustomVolumes) {
                    cookieCustomVolumes = {};
                }

                cookieCustomVolumes[$scope.currentTypeID] = $scope.customVolume;

                $cookies['customVolumes'] = angular.toJson(cookieCustomVolumes);

                updateCalculationUrl('customVolumes', $cookies['customVolumes']);
            } else {
                Notification.error($filter('translate')('volume_exist'));
            }
        };

        $scope.getMinVolume = function () {

            $scope.customVolume.minVolume = $scope.volumes[0].volume;

            if (!angular.isDefined($scope.customVolume.newVolume)) {
                $scope.customVolume.newVolume = $scope.volumes[0].volume;
            }
        };

        $scope.changeTax = function () {
            updateCalculationUrl('tax', $scope.productItem.taxID);
            $scope.getVolumes($scope.productItem.amount);
        };

        $scope.changeRealisationTime = function () {
            var idxRT = _.findIndex($scope.realisationTimes, {ID: $scope.productItem.realisationTime});

            if (idxRT !== -1) {

                var volume = $scope.productItem.volume;

                var idx = _.findIndex($scope.realisationTimes[idxRT].volumes, {volume: volume});
                if (idx !== -1) {
                    $scope.checkVolume(false, $scope.realisationTimes[idxRT], $scope.realisationTimes[idxRT].volumes[idx]);
                }

            }

        };

        $scope.filterRealisationTime = function (rt) {
            return rt.active ? 1 : 0;
        };

        $scope.getTotalThickness = function () {

            var tmp = 0;
            _.each($scope.summaryThickness, function (th) {
                tmp += th;
            });
            return tmp.toFixed(2);

        };

        $scope.toCart = function (addInBackground) {

            if ($scope.deliveryLackOfVolume > 0) {
                Notification.error($filter('translate')('delivery_lack_of_volume') + ': ' + $scope.deliveryLackOfVolume);
                return;
            }

            if ($scope.isAddToCartDisabled) {
                Notification.error($filter('translate')('cannot_add_to_cart_too_small_or_high_volume'));
                return;
            }

            getPreparedProduct($scope.productItem.amount, $scope.productItem.volume).then(function (preparedProduct) {
                AuthService.getSessionCarts().then(function (resData) {
                    if ($rootScope.logged) {
                        preparedProduct.orderID = undefined;
                    } else {
                        if (resData.orderID) {
                            preparedProduct.orderID = resData.orderID;
                        } else {
                            preparedProduct.orderID = undefined;
                        }
                    }
                }).then(function () {

                    DeliveryWidgetService.reducePostData($scope.productAddresses).then(function (productAddresses) {
                        DeliveryWidgetService.checkParcelShopSelected(productAddresses).then(function (productAddressesChecked) {

                            if (productAddressesChecked) {
                                if ($scope.type.allowCalcFilesUpload == 1) {
                                    if ($rootScope.logged === false) {
                                        preparedProduct.notLoggedCalcFilesSetID = $scope.calcFilesSetID;
                                    }
                                    preparedProduct.hasCalcFiles = true;
                                }
                                CalculateService = new CalculationService(preparedProduct.groupID, preparedProduct.typeID);
                                CalculateService.saveCalculation(preparedProduct).then(function (savedProduct) {

                                    if (savedProduct.orderID) {
                                        $rootScope.orderID = savedProduct.orderID;
                                    }

                                    savedProduct.productAddresses = productAddresses;
                                    var addData = savedProduct;
                                    if ($rootScope.logged) {
                                        addData.userID = $rootScope.user.userID;
                                        addData.token = '';
                                    } else {
                                        addData.userID = 0;
                                        addData.token = AuthDataService.getAccessToken();
                                    }
                                    DpCartsDataService.add(addData).then(function (response) {

                                        AuthService.addToCart(savedProduct).then(function (cartsData) {
                                            $rootScope.$emit('cartRequired');
                                            window.dataLayer = window.dataLayer || [];
                                            window.dataLayer.push({
                                                'event': 'eec.addToCart',
                                                'ecommerce': {
                                                    'currencyCode': $scope.calculation.currency.code,
                                                    'add': {
                                                        'products': [{
                                                            'name': $scope.currentType.name,
                                                            'id': $scope.calculation.groupID + '-' + $scope.calculation.typeID,
                                                            'price': $scope.calculation.priceTotalBrutto,
                                                            'quantity': $scope.calculation.volume
                                                        }]
                                                    }
                                                }
                                            });
                                            checkMatchAddress(cartsData.carts, productAddresses).then(function (cartToJoin) {
                                                if (addInBackground) {
                                                    Notification.success($filter('translate')('added_to_cart'));
                                                }
                                                if (cartToJoin) {
                                                    addToJoinedDelivery(productAddresses[0].addressID, $rootScope.currentCurrency.code).then(function (joinData) {

                                                        if (joinData.response) {
                                                            var tokenParams = {};

                                                            tokenParams['addressID'] = joinData.paramsToCopy.addressID;
                                                            tokenParams['active'] = true;
                                                            tokenParams['commonDeliveryID'] = joinData.paramsToCopy.commonDeliveryID;
                                                            tokenParams['commonRealisationTime'] = new Date(joinData.paramsToCopy.commonRealisationTime.sec * 1000);
                                                            TokenService.joinAddresses(tokenParams).then(function (data) {
                                                                if (!addInBackground) {
                                                                    $state.go('cart');
                                                                }
                                                            });
                                                        } else {
                                                            if (!addInBackground) {
                                                                $state.go('cart');
                                                            }
                                                        }
                                                    });
                                                } else {
                                                    if (!addInBackground) {
                                                        $state.go('cart');
                                                    }
                                                }

                                            });
                                        });
                                    });

                                }, function () {
                                    Notification.error($filter('translate')('error'));
                                });

                            } else {
                                Notification.error($filter('translate')('select_missing_parcel_shop'));
                            }


                        });
                    });
                });
            });

        };

        function checkMatchAddress(carts, productAddresses) {

            var def = $q.defer();

            if (productAddresses.length > 1) {
                def.resolve(false);
            }

            carts.pop();

            var addressID = productAddresses[0].addressID;
            var cartLen = carts.length;

            if (cartLen === 0) {
                def.resolve(false);
            }

            _.each(carts, function (cart, index) {
                if (cart.ProductAddresses.length === 1 && cart.ProductAddresses[0].addressID === addressID && cart.ProductAddresses[0].join === true) {
                    def.resolve(cart);
                }

                if (cartLen === index + 1) {
                    def.resolve(false);
                }
            });

            return def.promise;

        }

        function addToJoinedDelivery(addressID, currency) {
            var def = $q.defer();
            DpOrderService.addToJoinedDelivery(addressID, currency).then(function (data) {
                def.resolve(data);
            });
            return def.promise;
        }

        $scope.changeAmount = function () {
            if ($scope.productItem.amount === '') {
                $scope.productItem.amount = 1;
            }
            if (typeof $scope.productItem.amount === 'string') {
                if (isNaN(parseInt($scope.productItem.amount))) {
                    $scope.productItem.amount = 1;
                } else {
                    $scope.productItem.amount = parseInt($scope.productItem.amount);
                }
            }
            if ($scope.productItem.amount < 1) {
                $scope.productItem.amount = 1;
            }
            $scope.getVolumes($scope.productItem.amount);
        };

        $scope.hasFormats = function (desc) {

            var complexProducts = $scope.complexProducts;

            if (desc.formats.length > 0) {

                if (!angular.isDefined(complexProducts[0])) {
                    return true;
                }

                return _.includes(desc.formats, complexProducts[0].selectedProduct.data.currentFormat.ID);

            } else {
                return true;
            }

        };

        $scope.hasOneFormat = function (pattern) {

            if (!$scope.complexProducts || !$scope.complexProducts[0]) {
                return false;
            }

            return pattern.formatID === $scope.complexProducts[0].selectedProduct.data.currentFormat.ID;


        };

        function getDeliveries() {

            var def = $q.defer();

            DeliveryService.getAll($rootScope.currentCurrency.code).then(function (data) { //TODO currentCurrency can not exist
                $scope.deliveries = data;
                $scope.filteredDeliveries = _.clone(data);
                def.resolve(data);
            });

            return def.promise;

        }

        $rootScope.$watch('logged', function (logged) {
            if (logged != undefined) {
                loadData();
            }

        });

        function getAddress() {
            var def = $q.defer();

            if ($rootScope.logged) {

                AddressService.getForUser().then(function (data) {
                    def.resolve(data);
                });

            } else {
                AddressService.getAddressesFromSession().then(function (addresses) {
                    AddressService.getAll(addresses).then(function (data) {
                        def.resolve(data);
                    });
                });
            }

            return def.promise;
        }

        $scope.emptyArray = function (value) {
            return _.isArray(value) && _.isEmpty(value);
        };

        $scope.showSumPrice = () => CalcSimplifyWidgetService.showSumPrice($scope)

        $scope.showSumGrossPrice = () => CalcSimplifyWidgetService.showSumGrossPrice($scope)

        $scope.$watch('calculation.volume', function (value) {
            if (value === undefined) {
                return;
            }

            if ($scope.calculation.amount > 1) {
                value *= $scope.calculation.amount;
            }

            var address = $scope.productAddresses[0];

            DeliveryWidgetService.checkExclusions($scope, address);

            var existVolume = 0;
            _.each($scope.productAddresses, function (oneAddress, index) {
                if (index > 0) {
                    existVolume += Number(oneAddress.allVolume);
                }
            });

            if (existVolume >= value) {
                $scope.productAddresses.splice(1, $scope.productAddresses.length);
                existVolume = 0;
            }
            if (address !== undefined) {
                address.allVolume = (value - existVolume);
                if (typeof ($scope.calculation.weight) === 'number') {
                    address.weight = $scope.calculation.weight.toFixed(2).replace('.', ',');
                } else {
                    address.weight = parseFloat($scope.calculation.weight).toFixed(2).replace('.', ',');
                }
                if ($scope.senders[0] !== undefined) {
                    address.senderID = $scope.senders[0].type;
                }
                if ($scope.addresses[0] !== undefined) {
                    address.addressID = $scope.addresses[0].ID;
                }
                DeliveryWidgetService.getPkgWeightLite(
                    address,
                    DeliveryWidgetService.getVolume($scope, address),
                    $scope
                );
            }
        });

        $scope.getToken = function () {
            return AuthDataService.getAccessToken();
        };

        function getJson() {

            getPreparedProduct($scope.productItem.amount, $scope.productItem.volume).then(function (preparedProduct) {

                var result = {
                    typeID: preparedProduct.typeID,
                    products: [],
                    formats: [],
                    pages: [],
                    attributes: [],
                    name: $scope.productItem.name
                };
                _.each(preparedProduct.products, function (product, index) {
                    result.products.push(product.typeID);
                    result.formats.push(product.formatID);
                    result.pages.push(product.pages);
                    result.attributes[index] = [];
                    _.each(product.options, function (option) {
                        result.attributes[index].push(option.attrID + '-' + option.optID);
                    });
                });
                updateCalculationUrl('name', $scope.productItem.name);
                $scope.productItem.jsonText = JSON.stringify(result);

            });

        }

        $scope.changeUserProductName = function () {
            getJson();
        };

        $scope.printOffer = function () {

            TemplateRootService.getTemplateUrl(73).then(function (response) {

                $modal.open({
                    templateUrl: response.url,
                    scope: $scope,
                    size: 'lg',
                    controller: function ($scope) {

                        var Setting = new SettingService('general');

                        var numberOfVolumes = 5;

                        $scope.offerdate = new Date();
                        $scope.offer_exp_date = new Date();
                        $scope.offer_exp_date = $scope.offer_exp_date.setDate($scope.offerdate.getDate() + 30);

                        var url = '';
                        if (typeof $scope.galleries !== "undefined") {
                            if ($scope.galleries.length > 0 && $scope.galleries[0].files) {
                                url = $scope.galleries[0].files[0].url;
                            }
                        }

                        $scope.po_logo = url;

                        Setting.getPublicSettings().then(function (settingsData) {
                            if (settingsData.numberOfVolumesInOffer) {
                                numberOfVolumes = settingsData.numberOfVolumesInOffer.value;
                            }
                            getPreparedProduct($scope.productItem.amount, $scope.productItem.volume).then(function (data) {

                                $scope.offerdata = data;

                                if (data.products.length > 0 && $scope.complexProducts.length > 0) {
                                    var cps = new Array(data.products.length);

                                    for (var _idx = 0; _idx < data.products.length; ++_idx) {
                                        var _groupID = data.products[_idx].groupID;
                                        for (var i = 0; i < $scope.complexProducts.length; ++i) {

                                            var cp = $scope.complexProducts[i].selectedProduct;
                                            if (cp.groupID === _groupID) {
                                                cps[_idx] = cp;
                                            }
                                        }
                                    }

                                    $scope.offerdata.cps = cps;
                                }

                                if (typeof $scope.taxes !== "undefined") {
                                    if ($scope.taxes.length > 0) {
                                        var tax = "";
                                        for (i = 0; i < $scope.taxes.length; ++i) {
                                            if ($scope.taxes[i].ID === data.taxID) {
                                                tax = $scope.taxes[i].name;
                                            }
                                        }
                                        $scope.offerdata.tax = tax;
                                    }
                                }

                                var rt;
                                if ($scope.realisationTimes !== undefined) {
                                    if (data.realizationTimeID !== undefined) {
                                        rt = _.find($scope.realisationTimes, {ID: data.realizationTimeID});
                                        $scope.offerdata.realizationTime = rt.name;
                                    } else {
                                        $scope.offerdata.realizationTime = "";
                                    }

                                }

                                var index = 0;

                                rt.volumes = _(rt.volumes).chain().filter(function (oneVolume) {
                                    return oneVolume.active === true;
                                }).sortBy(function (oneVolume) {
                                    return oneVolume.volume;
                                }).value();

                                var actualVolumeIndex = _.findIndex(rt.volumes, {volume: data.volume});

                                var halfOfVolumes;
                                var firstIndex;
                                var lastIndex;

                                if (numberOfVolumes >= (rt.volumes.length - 1)) {
                                    firstIndex = 0;
                                    lastIndex = rt.volumes.length - 1;
                                } else {

                                    halfOfVolumes = parseInt(numberOfVolumes / 2);
                                    firstIndex = actualVolumeIndex - halfOfVolumes;
                                    lastIndex = firstIndex + (numberOfVolumes - 1);

                                    if (firstIndex < 0) {
                                        firstIndex = 0;
                                        lastIndex = firstIndex + (numberOfVolumes - 1);
                                    }

                                    if (lastIndex > (rt.volumes.length - 1)) {
                                        lastIndex = rt.volumes.length - 1;
                                        firstIndex = lastIndex - (numberOfVolumes - 1);
                                    }

                                }

                                var filteredVolumes = {};
                                var tmpPrice;
                                var tmpPriceGross;

                                for (index; index < rt.volumes.length; ++index) {

                                    if (index >= firstIndex && index <= lastIndex) {
                                        var q = rt.volumes[index].volume;
                                        var n = rt.volumes[index].price;
                                        var g = rt.volumes[index].priceBrutto;
                                        var ns = n;
                                        var gs = g;
                                        if (q > 1) {
                                            if (typeof n === 'string') {
                                                n = n.replace(',', '.');
                                            }
                                            if (typeof g === 'string') {
                                                g = g.replace(',', '.');
                                            }
                                            ns = parseFloat(n) / q;
                                            gs = parseFloat(g) / q;
                                            ns = ns.toFixed(2);
                                            gs = gs.toFixed(2);
                                        }

                                        tmpPrice = ns;
                                        if (typeof tmpPrice === 'string') {
                                            tmpPrice = tmpPrice.replace(".", ",");
                                        }
                                        tmpPriceGross = gs;
                                        if (typeof tmpPriceGross === 'string') {
                                            tmpPriceGross = tmpPriceGross.replace(".", ",");
                                        }
                                        filteredVolumes[index] = {
                                            qty: q,
                                            net: n,
                                            gross: g,
                                            netunit: tmpPrice,
                                            grossunit: tmpPriceGross
                                        };
                                    }

                                    if (rt.volumes[index].active === false) {
                                        --lastIndex;
                                    }

                                }

                                $scope.rtVolumes = filteredVolumes;

                                $scope.print = function () {

                                    var CalculateDataObject = new CalculateDataService(data.typeID);

                                    var dataForPrint = {
                                        amount: data.amount,
                                        groupID: data.groupID,
                                        typeID: data.typeID,
                                        products: data.products,
                                        customVolumes: data.customVolumes,
                                        taxID: data.taxID,
                                        currency: data.currency,
                                        productAddresses: data.productAddresses,
                                        activeVolume: data.volume,
                                        realizationTimeID: data.realizationTimeID
                                    };
                                    if (data.userID) {
                                        dataForPrint.userID = data.userID;
                                    }
                                    if (data.selectedTechnology) {
                                        dataForPrint.selectedTechnology = data.selectedTechnology;
                                    }
                                    CalculateDataObject.printOffer(dataForPrint).then(function (processedData) {
                                        if (processedData.success === true) {
                                            $window.open(processedData.link, '_blank');
                                        }
                                    });

                                }

                            });

                        });

                    }
                });

            });
        };

        $scope.showRealizationTime = function (realizationTimeID) {
            var rIdx = _.findIndex($scope.realisationTimes, {ID: realizationTimeID});
            var resDate = '';
            if (rIdx > -1) {
                if ($scope.realisationTimes[rIdx].overwriteDate !== undefined && $scope.realisationTimes[rIdx].overwriteDate !== null) {
                    resDate = $scope.realisationTimes[rIdx].overwriteDate;
                } else {
                    resDate = $scope.realisationTimes[rIdx].date;
                }
            }
            return resDate;
        };

        $scope.releaseSpinner = function (complexProduct, attrID, direct) {

            if (complexProduct.selectedProduct.data.attrPages[attrID] <= 0 && direct === 0) {
                return;
            }

            var attrIdx = _.findIndex(complexProduct.selectedProduct.data.attributes, {attrID: parseInt(attrID)});

            if (attrIdx > -1) {
                var attribute = complexProduct.selectedProduct.data.attributes[attrIdx];

                var step = attribute.step;

                var maxPages = attribute.maxPages;
                if (maxPages === null) {
                    maxPages = complexProduct.selectedProduct.data.currentPages;
                }

                if ((complexProduct.selectedProduct.data.attrPages[attrID] + step) > maxPages && direct === 1) {
                    Notification.info($filter('translate')('maximum_number_of_pages') + ' ' + maxPages);
                    return;
                }

                if ((complexProduct.selectedProduct.data.attrPages[attrID] - step) < attribute.minPages && direct === 0) {
                    Notification.info($filter('translate')('minimum_number_of_pages') + ' ' + attribute.minPages);
                    return;
                }
            }

            if (direct) {
                complexProduct.selectedProduct.data.attrPages[attrID] += step;
            } else {
                complexProduct.selectedProduct.data.attrPages[attrID] -= step;
            }

            $scope.selectAttrPages(complexProduct, attrID);
        };

        $scope.spinPage = function (complexProduct, direct) {
            $scope.selectPages(complexProduct.selectedProduct.data, complexProduct.selectedProduct.data.currentPages + (direct ? 1 : -1) * complexProduct.selectedProduct.data.pages[0].step);
        };

        $scope.selectCustomFormat = function (complexProduct) {

            complexProduct.selectedProduct.data.currentFormat.customHeight = Number(complexProduct.selectedProduct.data.currentFormat.customHeight);
            complexProduct.selectedProduct.data.currentFormat.customWidth = Number(complexProduct.selectedProduct.data.currentFormat.customWidth);
            updateCalculationUrl('customWidth', complexProduct.selectedProduct.data.currentFormat.customWidth, null, productIndex(complexProduct));
            updateCalculationUrl('customHeight', complexProduct.selectedProduct.data.currentFormat.customHeight, null, productIndex(complexProduct));
            if (angular.isDefined(stopSelect)) {
                $timeout.cancel(stopSelect);
                stopSelect = undefined;
            }

            stopSelect = $timeout(function () {

                // check maximal and minimal customSize
                var minHeight = complexProduct.selectedProduct.data.currentFormat.minHeight - complexProduct.selectedProduct.data.currentFormat.slope * 2;
                var minWidth = complexProduct.selectedProduct.data.currentFormat.minWidth - complexProduct.selectedProduct.data.currentFormat.slope * 2;

                var maxHeight = complexProduct.selectedProduct.data.currentFormat.maxHeight - complexProduct.selectedProduct.data.currentFormat.slope * 2;
                var maxWidth = complexProduct.selectedProduct.data.currentFormat.maxWidth - complexProduct.selectedProduct.data.currentFormat.slope * 2;

                if (complexProduct.selectedProduct.data.currentFormat.customHeight > maxHeight) {
                    Notification.info($filter('translate')('value_greater_than_maximum') + ' ' + maxHeight);
                    complexProduct.selectedProduct.data.currentFormat.customHeight = maxHeight;
                }

                if (complexProduct.selectedProduct.data.currentFormat.customHeight < minHeight) {
                    Notification.info($filter('translate')('value_lower_than_minimum') + ' ' + minHeight);
                    complexProduct.selectedProduct.data.currentFormat.customHeight = minHeight;
                }

                if (complexProduct.selectedProduct.data.currentFormat.customWidth > maxWidth) {
                    Notification.info($filter('translate')('value_greater_than_maximum') + ' ' + maxWidth);
                    complexProduct.selectedProduct.data.currentFormat.customWidth = maxWidth;
                }

                if (complexProduct.selectedProduct.data.currentFormat.customWidth < minWidth) {
                    Notification.info($filter('translate')('value_lower_than_minimum') + ' ' + minWidth);
                    complexProduct.selectedProduct.data.currentFormat.customWidth = minWidth;
                }

                // depth notification when lower,  higher
                if (complexProduct.selectedProduct.data.currentFormat.customDepth > complexProduct.selectedProduct.data.currentFormat.maxDepth) {
                    Notification.info($filter('translate')('value_greater_than_maximum') + ' ' + complexProduct.selectedProduct.data.currentFormat.maxDepth);
                    complexProduct.selectedProduct.data.currentFormat.customDepth = complexProduct.selectedProduct.data.currentFormat.maxDepth;
                }
                if (complexProduct.selectedProduct.data.currentFormat.customDepth < complexProduct.selectedProduct.data.currentFormat.minDepth) {
                    Notification.info($filter('translate')('value_lower_than_minimum') + ' ' + complexProduct.selectedProduct.data.currentFormat.minDepth);
                    complexProduct.selectedProduct.data.currentFormat.customDepth = complexProduct.selectedProduct.data.currentFormat.minDepth;
                }

                $scope.getVolumes($scope.productItem.amount);

            }, 1500);
        };

        $scope.spinCustomHeight = function (complexProduct, direct) {
            if (direct) {
                complexProduct.selectedProduct.data.currentFormat.customHeight = complexProduct.selectedProduct.data.currentFormat.customHeight + complexProduct.selectedProduct.data.currentFormat.heightStep || 1;
            } else {
                complexProduct.selectedProduct.data.currentFormat.customHeight = complexProduct.selectedProduct.data.currentFormat.customHeight - complexProduct.selectedProduct.data.currentFormat.heightStep || 1;
            }

            $scope.selectCustomFormat(complexProduct);

        };

        $scope.spinCustomDepth = function (complexProduct, direct) {

            if (direct) {
                complexProduct.selectedProduct.data.currentFormat.customDepth = complexProduct.selectedProduct.data.currentFormat.customDepth + complexProduct.selectedProduct.data.currentFormat.depthStep || 1;
            } else {
                complexProduct.selectedProduct.data.currentFormat.customDepth = complexProduct.selectedProduct.data.currentFormat.customDepth - complexProduct.selectedProduct.data.currentFormat.depthStep || 1;
            }

            $scope.selectCustomFormat(complexProduct);

        };
                $scope.spinCustomWidth = function (complexProduct, direction) {

            if (direction) {
                complexProduct.selectedProduct.data.currentFormat.customWidth = complexProduct.selectedProduct.data.currentFormat.customWidth + complexProduct.selectedProduct.data.currentFormat.widthStep || 1;
            } else {
                complexProduct.selectedProduct.data.currentFormat.customWidth = complexProduct.selectedProduct.data.currentFormat.customWidth - complexProduct.selectedProduct.data.currentFormat.widthStep || 1;
            }

            $scope.selectCustomFormat(complexProduct);

        };

        $scope.spinCustomAmount = function (direct) {

            if (direct) {
                $scope.productItem.amount = $scope.productItem.amount + 1;
            } else {

                if ($scope.productItem.amount === 1) {
                    return;
                }

                $scope.productItem.amount = $scope.productItem.amount - 1;
            }

            $scope.changeAmount();

        };

        $scope.spinWingtip = function (complexProduct, direction, field) {
            complexProduct.selectedProduct.data.currentFormat[field] = Number(complexProduct.selectedProduct.data.currentFormat[field]) + direction;
            $scope.selectWingtip(complexProduct);
        };

        $scope.selectWingtip = function (complexProduct) {
            complexProduct.selectedProduct.data.currentFormat.wingtipFront = Number(complexProduct.selectedProduct.data.currentFormat.wingtipFront);
            complexProduct.selectedProduct.data.currentFormat.wingtipBack = Number(complexProduct.selectedProduct.data.currentFormat.wingtipBack);
            updateCalculationUrl('wingtipFront', complexProduct.selectedProduct.data.currentFormat.wingtipFront, null, productIndex(complexProduct));
            updateCalculationUrl('wingtipBack', complexProduct.selectedProduct.data.currentFormat.wingtipBack, null, productIndex(complexProduct));
            if (angular.isDefined(stopSelect)) {
                $timeout.cancel(stopSelect);
                stopSelect = undefined;
            }
            var minSize = [complexProduct.selectedProduct.data.currentFormat.wingtipFrontMin, complexProduct.selectedProduct.data.currentFormat.wingtipBackMin];
            var maxWidth = complexProduct.selectedProduct.data.currentFormat.width - 2 * 10;
            stopSelect = $timeout(function () {
                if (complexProduct.selectedProduct.data.currentFormat.wingtipFront < minSize[0]) {
                    Notification.info($filter('translate')('value_lower_than_minimum') + ' ' + minSize[0]);
                    complexProduct.selectedProduct.data.currentFormat.wingtipFront = minSize[0];
                }
                if (complexProduct.selectedProduct.data.currentFormat.wingtipBack < minSize[1]) {
                    Notification.info($filter('translate')('value_lower_than_minimum') + ' ' + minSize[1]);
                    complexProduct.selectedProduct.data.currentFormat.wingtipBack = minSize[1];
                }
                if (complexProduct.selectedProduct.data.currentFormat.wingtipFront > maxWidth) {
                    Notification.info($filter('translate')('value_greater_than_maximum') + ' ' + maxWidth);
                    complexProduct.selectedProduct.data.currentFormat.wingtipFront = maxWidth;
                }
                if (complexProduct.selectedProduct.data.currentFormat.wingtipBack > maxWidth) {
                    Notification.info($filter('translate')('value_greater_than_maximum') + ' ' + maxWidth);
                    complexProduct.selectedProduct.data.currentFormat.wingtipBack = maxWidth;
                }
                $scope.getVolumes($scope.productItem.amount);

            }, 1500);
            timeouts.push(stopSelect);
        };

        $scope.optionsSort = function (option) {
            return option.sort;
        };

        $rootScope.$on('Currency.changed', function (e, currency) {

            $scope.getVolumes($scope.productItem.amount);
            getDeliveries();

        });

        $scope.showAttribute = function (complexProduct, attrID) {
            var attrIdx = _.findIndex(complexProduct.selectedProduct.data.attributes, {attrID: parseInt(attrID)});
            var attrName;
            if (attrIdx > -1) {
                var attribute = complexProduct.selectedProduct.data.attributes[attrIdx];

                var optID = complexProduct.selectedProduct.data.selectedOptions[attribute.attrID];

                var optIdx = _.findIndex(attribute.filteredOptions, {ID: parseInt(optID)});
                if (optIdx > -1) {
                    var option = attribute.filteredOptions[optIdx];

                    if (option.invisible === 1) {
                        return '';
                    }

                } else {
                    return '';
                }

                if (attribute.names[$rootScope.currentLang.code].name !== undefined) {
                    attrName = attribute.names[$rootScope.currentLang.code].name
                } else {
                    attrName = attribute.attrName;
                }

                return attrName;

            }
            return '';
        };

        $scope.showOption = function (complexProduct, attrID) {
            var attrIdx = _.findIndex(complexProduct.selectedProduct.data.attributes, {attrID: parseInt(attrID)});
            var optionName;
            if (attrIdx > -1) {
                var attribute = complexProduct.selectedProduct.data.attributes[attrIdx];

                var optID = complexProduct.selectedProduct.data.selectedOptions[attribute.attrID];

                var optIdx = _.findIndex(attribute.filteredOptions, {ID: parseInt(optID)});
                if (optIdx > -1) {
                    var option = attribute.filteredOptions[optIdx];

                    if (option.invisible === 1) {
                        return '';
                    }

                    if (option.names[$rootScope.currentLang.code].name !== undefined) {
                        optionName = option.names[$rootScope.currentLang.code].name;
                    } else {
                        optionName = option.name;
                    }

                    return optionName;
                }
            }
            return '';
        };

        $scope.showTax = function (taxID) {

            var idxTax = _.findIndex($scope.taxes, {ID: taxID});

            if (idxTax > -1) {
                return $scope.taxes[idxTax].value + ' %';
            }
        };

        $scope.checkEmptyChoice = function (complexProduct, attributeID) {

            var attrIdx = _.findIndex(complexProduct.selectedProduct.data.attributes, {attrID: parseInt(attributeID)});

            if (attrIdx > -1) {
                var attribute = complexProduct.selectedProduct.data.attributes[attrIdx];

                var optionID = complexProduct.selectedProduct.data.selectedOptions[attribute.attrID];

                var optIdx = _.findIndex(attribute.filteredOptions, {ID: parseInt(optionID)});
                if (optIdx > -1) {
                    var option = attribute.filteredOptions[optIdx];
                    return option.emptyChoice;
                }

                return false;
            }

            return false;
        };

        $scope.toggleShowPattern = function () {
            $scope.showPattern = true;
            $scope.showSummary = false;
        };

        $scope.toggleShowSummary = function () {
            $scope.showSummary = true;
            $scope.showPattern = false;
        };

        $scope.selectType = function (item) {
            if (item) {

                PsTypeService.getOneForView(
                    item.group.slugs[$rootScope.currentLang.code],
                    item.slugs[$rootScope.currentLang.code]
                ).then(function (typeInfo) {

                    var categorySlugs = {};
                    _.each(typeInfo.category.langs, function (langObject, lang) {
                        categorySlugs[lang] = langObject.url;
                    });
                    if ($rootScope.urlParams === undefined) {
                        $rootScope.urlParams = {};
                    }
                    $rootScope.urlParams.category = categorySlugs;
                    $rootScope.urlParams.group = typeInfo.group.slugs;
                    $rootScope.urlParams.type = typeInfo.slugs;

                    var urlParams = {};

                    if ($stateParams.categoryurl === undefined && $stateParams.groupurl === undefined) {
                        urlParams = {
                            typeurl: typeInfo.slugs[$rootScope.currentLang.code]
                        };
                    } else if ($stateParams.categoryurl === undefined && $stateParams.groupurl !== undefined) {
                        urlParams = {
                            groupurl: typeInfo.group.slugs[$rootScope.currentLang.code],
                            typeurl: typeInfo.slugs[$rootScope.currentLang.code]
                        };
                    } else {
                        urlParams = {
                            categoryurl: typeInfo.category.langs[$rootScope.currentLang.code].url,
                            groupurl: typeInfo.group.slugs[$rootScope.currentLang.code],
                            typeurl: typeInfo.slugs[$rootScope.currentLang.code]
                        };
                    }

                    if (typeInfo.isEditor) {
                        $state.go('select-project', urlParams);
                    } else {
                        $state.go('calculate', urlParams);
                    }

                });
            }
        };

        function descriptionTabResetActive() {
            $timeout(function () {
                $('.with-nav-tabs .nav-tabs li').removeClass('active');
                $('.with-nav-tabs .tab-content div.tab-pane').removeClass('active');

                $('.with-nav-tabs .nav-tabs li').first().addClass('active');
                $('.with-nav-tabs .tab-content div.tab-pane').first().addClass('active');
            }, 300);
        }

        function updateCalculationUrl(name, value, nameGroup, index) {
            $scope.quotationSend = false;
            if (arguments.length > 2 && nameGroup) {
                name += '.' + nameGroup;
            }
            if (arguments.length > 3) {
                name += '.' + index;
            }
            $location.search(name, value);
            updateLinkToCopy();
        }

        function setFromCalculationUrl(item, propertyName, storedPropertyName, defaultValue, converter, reset) {
            var formatValue = function (value) {
                if (converter) {
                    value = converter(value);
                }
                return value;
            };
            var changes = [];
            if (storedPropertyName.indexOf('[]') > -1) {
                var params = $location.search();
                storedPropertyName = storedPropertyName.replace('[]', '');
                for (var key in params) {
                    var keyParts = key.split('.')
                    if (keyParts[0] === storedPropertyName) {
                        if (keyParts.length == 2) {
                            var index = keyParts[1]
                            var path = propertyName.split('.')
                            var goal = item[index];
                            for (var i = 0; i < path.length - 1; i++) {
                                goal = goal[path[i]]
                            }
                            try{
                                goal[path[path.length - 1]] = formatValue(params[key]);
                            }catch (e) {
                                console.log(e)
                                throw new Error(e)
                            }

                            log.debug('setFromCalculationUrl', index, path, key, params);
                        } else if (keyParts.length == 3) {
                            var propertyNameParts = propertyName.split('.')
                            var goal = item[keyParts[2]]
                            for (var i = 0; i < propertyNameParts.length; i++) {
                                if (goal) {
                                    goal = goal[propertyNameParts[i]]
                                } else {
                                    throw new Error('Wrong goal for propertyName ' + propertyName);
                                }

                            }
                            goal[keyParts[1]] = formatValue(params[key]);
                            changes.push([goal, keyParts[2], keyParts[1], goal[keyParts[1]]]);
                            log.debug('setFromCalculationUrl', index, propertyNameParts, key, params);
                        }

                    }
                }
            } else {
                var value = $location.search()[storedPropertyName] || defaultValue
                if (value) {
                    item[propertyName] = formatValue(value);
                    log.debug('setFromCalculationUrl', propertyName, value);
                }
            }
            if (reset) {
                updateCalculationUrl(storedPropertyName, null)
            }
            return changes;
        }

        function getCalculationUrlParam(storedPropertyName) {
            return $location.search()[storedPropertyName]
        }

        function setupClipboardJS() {
            var clipboardJS = new ClipboardJS('#copyCalculationUrlBtn')
            clipboardJS.on('success', function (e) {
                log.info('Url copied');
            });
            clipboardJS.on('error', function (e) {
                log.error('Copy Url', e);
            });
        }

        function updateLinkToCopy() {
            var elRef = document.querySelector('#copyCalculationUrlBtn')
            if (elRef) {
                elRef.setAttribute('data-clipboard-text', $location.absUrl())
            }
        }

        function getCartUrl() {
            return document.querySelector('#copyCalculationUrlBtn').getAttribute('data-clipboard-text');
        }

        $scope.selectOptionImage = function (complexProductData, item, attribute) {
            complexProductData.selectedOptions[attribute.attrID] = item.ID;
            $scope.selectOption(complexProductData, attribute.attrID);
        };

        $scope.setOptionPicture = function ($event, item) {
            $scope.optionPicture = item.icon;
            setTimeout(function () {
                $('#showOptionPicture').modal('show');
                $event.stopPropagation();
            }, 100);

        };

        $scope.filterSearchProduct = function () {

            var _that = this;

            if (this.query === undefined) {
                return;
            }

            if (!this.query.productName) {
                $scope.filteredProducts = $rootScope.allTypes;
            } else {
                $('.dropdown-menu.option:hidden').dropdown("toggle");
                $scope.filteredProducts = _.filter($rootScope.allTypes, function (one) {

                    if (one.names === undefined || one.names[$rootScope.currentLang.code] === undefined) {
                        return false;
                    }

                    return one.names[$rootScope.currentLang.code].toLowerCase().search(_that.query.productName.toLowerCase()) > -1;

                });
            }
        };

        $scope.getFlagClass = function (addresses, addressID) {
            var selectedAddress = _.find(addresses, {ID: addressID});
            if (selectedAddress) {
                return 'flag-icon-' + selectedAddress.countryCode.toLowerCase();
            }
            return '';
        };

        $scope.selectTechnology = function () {
            updateCalculationUrl('technologyID', this.productItem.selectedTechnologyID);
            $scope.getVolumes($scope.productItem.amount);
        };

        $scope.showTechnologyTooltip = function (technology) {

            if (!technology || technology.names === undefined) {
                return '';
            }

            if (!technology.selected) {
                return $filter('translate')('count_only_for') + ' ' + technology.names[$rootScope.currentLang.code];
            }

            return $filter('translate')('count_for_all_technologies');
        };

        function formatTextProductConfiguration() {
            var texts = [];
            _.each($scope.complexProducts, function (complexProduct) {
                var data = complexProduct.selectedProduct.data;
                if ($scope.complexProducts.length > 1) {
                    texts.push([data.info.langs[$scope.currentLang.code].name])
                }
                // texts.push([data.customFormatInfo.customName[$scope.currentLang.code]])
                if (data.currentFormat.custom) {
                    texts.push([$filter('translate')('format'), data.currentFormat.name + ' (' + data.currentFormat.customWidth + ' x ' + data.currentFormat.customHeight + ')'])
                } else {
                    texts.push([$filter('translate')('format'), data.currentFormat.name])
                }
                texts.push([$filter('translate')('pages'), data.currentPages])
                _.each(complexProduct.selectedProduct.data.attributes, function (attribute) {
                    if (attribute.filteredOptions && attribute.filteredOptions.length > 0) {
                        var addToArray = true;
                        _.each(attribute.filteredOptions, function (filteredOption) {
                            if (filteredOption.emptyChoice) {
                                addToArray = false;
                            }
                        });
                        if (addToArray === true) {
                            texts.push([$scope.showAttribute(complexProduct, attribute.attrID), $scope.showOption(complexProduct, attribute.attrID)])
                        }
                    }
                });
                texts.push([$filter('translate')('volume'), $scope.productItem.amount])
                texts.push([$filter('translate')('vat_value'), $scope.showTax($scope.productItem.taxID)])
            });
            texts = _.map(texts, function (text) {
                if (text.length === 2) {
                    if (text[0] && text[1] && text[0] !== '' && text[1] !== '') {
                        return text[0] + ': ' + text[1];
                    }
                    return '';
                } else if (text.length === 1) {
                    return text[0];
                }
            });
            return texts.join("\n");
        }

        $scope.sendQuotation = function () {
            getPreparedProduct($scope.productItem.amount, $scope.productItem.volume).then(function (preparedProduct) {
                CalculateService = new CalculationService(preparedProduct.groupID, preparedProduct.typeID);
                preparedProduct.isOffer = 1;
                preparedProduct.isQuestion = 1;
                CalculateService.saveCalculation(preparedProduct).then(function (data) {
                    var productQuestion = {
                        name: $scope.currentType.names[$scope.currentLang.code],
                        content: formatTextProductConfiguration() + "\n" + getCartUrl(),
                        groupID: $scope.currentGroupID,
                        typeID: $scope.currentTypeID,
                        calcID: data.calcID
                    };
                    CustomProductService.add(productQuestion).then(function (savedData) {
                        if (savedData.response === true) {
                            Notification.success($filter('translate')('question_send'));
                            $scope.quotationSend = true;
                            $scope.quotationItemID = savedData.item.ID;
                        }
                    }, function () {
                        Notification.error($filter('translate')('error'));
                    });
                });
            });

        };

        $scope.login = function (credentials) {
            var backTo = {
                state: 'calculate',
                params: {
                    categoryurl: $state.params.categoryurl,
                    groupurl: $state.params.groupurl,
                    typeurl: $state.params.typeurl
                }
            };
            LoginWidgetService.login(credentials, backTo);
        };

        $scope.includedAlternatives = false;

        $scope.includeAlternatives = function () {
            $scope.includedAlternatives = !$scope.includedAlternatives;
        }

        $scope.includeAlternativesOn = function () {
            $scope.includedAlternatives = true;
        }

        $scope.filterAlternatives = function (items) {
            return _.filter(items, function (item) {
                return $scope.includedAlternatives ? true : !item.isAlternative
            });
        }

        $scope.checkForAlts = function (attribute, complexProduct) {
            var selectedOption = complexProduct.selectedProduct.data.selectedOptions[attribute.attrID];
            var allOptions = attribute.options;
            var altOptions = _.filter(allOptions, function (item) {
                return item.isAlternativeOf === selectedOption;
            });
            return altOptions.length;
        }

        $scope.showAltPapers = function (attribute, complexProduct) {
            var selectedOption = complexProduct.selectedProduct.data.selectedOptions[attribute.attrID];
            var allOptions = attribute.options;
            var altOptions = _.filter(allOptions, function (item) {
                return item.isAlternativeOf === selectedOption;
            });
            var selectedOptionInstance = _.filter(allOptions, function (item) {
                return item.ID === selectedOption;
            });
            console.log(complexProduct);
            console.log(attribute);

            if (altOptions.length > 0) {
                TemplateRootService.getTemplateUrl(129).then(function (response) {
                    $modal.open({
                        templateUrl: response.url,
                        scope: $scope,
                        size: 'lg',
                        controller: function ($scope, $modalInstance) {
                            $scope.selectedOptionInstance = selectedOptionInstance;
                            $scope.altOptions = altOptions;
                            $scope.chooseAltOption = function (option) {
                                $scope.includeAlternativesOn();
                                complexProduct.selectedProduct.data.selectedOptions[attribute.attrID] = option.ID;
                                $scope.selectOption(complexProduct.selectedProduct.data, attribute.attrID);
                                $modalInstance.close();
                            };
                        }
                    });

                });
            } else {
                Notification.error($filter('translate')('no_alternative_options_for_this_option'));
            }
        };

        $scope.uploadFiles = function (product) {

            TemplateRootService.getTemplateUrl(34).then(function (response) {
                $modal.open({
                    templateUrl: response.url,
                    scope: $scope,
                    backdrop: true,
                    keyboard: false,
                    size: 'lg',
                    resolve: {
                        allowedExtensions: function () {
                            return CommonService.getAll().then(function (data) {
                                var extensions = [];
                                _.each(data, function (item) {
                                    extensions.push(item['extension']);
                                });

                                return extensions;

                            });
                        }
                    },
                    controller: function ($scope, $modalInstance, allowedExtensions, $config) {

                        var accessTokenName = $config.ACCESS_TOKEN_NAME;

                        var header = {};
                        header[accessTokenName] = AuthDataService.getAccessToken();

                        var calcFilesSetID = '';
                        if ($rootScope.logged === false && $scope.calcFilesSetID) {
                            calcFilesSetID = '/' + $scope.calcFilesSetID;
                        }

                        var uploader = $scope.uploader = new FileUploader({
                            'url': CalcFileService.getUrl($scope.currentTypeID) + calcFilesSetID,
                            'headers': header
                        });

                        console.log({uploader});

                        uploader.filters.push({
                            name: 'imageFilter',
                            fn: function (item, options) {
                                var itemName = item.name.split('.');
                                var lastItem = itemName.pop().toLowerCase();

                                if (allowedExtensions.indexOf(lastItem) > -1) {
                                    return true;
                                }
                                Notification.warning($filter('translate')('required_ext') + allowedExtensions.join(', '));
                                return false;
                            }
                        });

                        uploader.onAfterAddingAll = function (addedItems) {
                            uploader.uploadAll();
                        };

                        uploader.onSuccessItem = function (fileItem, response, status) {
                            console.log(response);
                            $scope.calcFiles.push(response.file);
                            var calcFilesSetID = response.file.calcFilesSetID;
                            localStorageService.set('calcFilesSetID', calcFilesSetID);
                            $scope.calcFilesSetID = calcFilesSetID;
                            $scope.setPagination($scope.calcFilesCurrentPage);
                            // $scope.calculate($scope.productItem.amount, 209);

                        };

                        uploader.onCompleteAll = function () {
                            // $modalInstance.close();

                        };

                        uploader.onClose = function () {
                            console.log('asdasdasd');

                        };

                        $scope.cancel = function () {
                            if (uploader.isUploading) {
                                alert($filter('translate')('uploading_in_progress'));
                            } else {
                                $modalInstance.close();
                            }
                        }
                    }
                }).result.finally(function () {
                    $scope.setNewVolume(caclulateCalcFilesVolume());
                });
                ;
            });
        };

        $scope.removeFile = function (fileID) {
            CalcFileService.removeFile($scope.type.ID, fileID).then(caclFilesData => {


                var index = _.findIndex($scope.calcFiles, {ID: fileID});
                if (index === -1) {
                    return true;
                }

                if ($scope.calcFiles[index].isLastInGroup && $scope.calcFiles[index - 1].isFirstInGroup) {
                    $scope.calcFiles[index - 1].copies = 0;
                } else if ($scope.calcFiles[index].isLastInGroup && !$scope.calcFiles[index - 1].isFirstInGroup && !$scope.calcFiles[index - 1].isLastInGroup) {
                    $scope.calcFiles[index - 1].isLastInGroup = true;
                } else if ($scope.calcFiles[index].isFirstInGroup && $scope.calcFiles[index].copies > 0) {
                    if ($scope.calcFiles[index].copies == 1) {
                        $scope.calcFiles[index + 1].copies = 0;
                        $scope.calcFiles[index + 1].isFirstInGroup = true;
                        $scope.calcFiles[index + 1].isLastInGroup = false;
                    } else {
                        $scope.calcFiles[index + 1].copies = 1;
                        $scope.calcFiles[index + 1].isFirstInGroup = true;
                        $scope.calcFiles[index + 1].isLastInGroup = false;
                    }

                    _.forEach($scope.calcFiles, function (calcFile) {
                        if (calcFile.copyOf == $scope.calcFiles[index].ID) {
                            var index2 = _.findIndex($scope.calcFiles, {ID: calcFile.ID});
                            if (index2 === -1) {
                                return true;
                            }
                            console.log(index2);
                            console.log($scope.calcFiles[index2]);
                            console.log($scope.calcFiles[index + 1]);
                            $scope.calcFiles[index2].copyOf = $scope.calcFiles[index + 1].ID;
                        }
                    });
                    console.log($scope.calcFiles);
                }


                _.remove($scope.calcFiles, {ID: caclFilesData.removed_item.ID});
                $scope.setNewVolume(caclulateCalcFilesVolume());
                $scope.setPagination($scope.calcFilesCurrentPage);
            });
        };

        $scope.removeAllFiles = function () {
            _.forEach($scope.calcFiles, function (calcFile) {
                CalcFileService.removeFile($scope.type.ID, calcFile.ID).then(function (caclFilesData) {
                    _.remove($scope.calcFiles, {ID: caclFilesData.removed_item.ID});
                    if ($scope.calcFiles.length === 0) {
                        $scope.setNewVolume(caclulateCalcFilesVolume());
                        $scope.productItem.volume = 0;
                        $scope.changeVolume();
                        $scope.setPagination(1);
                    }
                });
            });
        };

        $scope.setNewVolume = function (volume) {
            $scope.isAddToCartDisabled = true;
            if (parseInt($scope.customVolume.maxVolume) < parseInt(volume)) {
                Notification.error($filter('translate')('to_high_volume') + ' - ' + $scope.customVolume.maxVolume);
                return;
            }

            if (parseInt($scope.customVolume.minVolume) > parseInt(volume)) {
                Notification.error($filter('translate')('to_low_volume') + ' - ' + $scope.customVolume.minVolume);
                return;
            }

            if (volume === undefined) {
                Notification.error($filter('translate')('incorrect_volume'));
                return;
            }

            var newVolume = {'volume': volume, 'active': true};
            $scope.customVolume.volumes = [newVolume];
            $scope.rememberVolume.volume = newVolume;
            $scope.getVolumes($scope.productItem.amount);
            $scope.isAddToCartDisabled = false;
        };
        function copyGroupProperties(file) {
            var copies = file.copies;
            var isFirstInGroup = file.isFirstInGroup;
            var isLastInGroup = file.isLastInGroup;

            return {copies, isFirstInGroup, isLastInGroup};
        }

        function setGroupProperties(properties, index) {
            $scope.calcFiles[index].copies = properties.copies;
            $scope.calcFiles[index].isFirstInGroup = properties.isFirstInGroup;
            $scope.calcFiles[index].isLastInGroup = properties.isLastInGroup;
        }

        function setAddress(allAddress) {
            $scope.addresses = allAddress.addresses;
            if (_.size(allAddress.senders) > 0) {
                $scope.senders = [];
                _.each(allAddress.senders, function (item) {
                    item.name = $filter('translate')(item.name);
                    $scope.senders.push(item);
                });
            }
        }

        $scope.setImageBW = function (file) {
            CalcFileService.setImageBW(file.ID).then(function (data) {
                console.log(data);
                var index = _.findIndex($scope.calcFiles, {ID: file.ID});
                if (index === -1) {
                    return true;
                }
                var groupProperties = copyGroupProperties($scope.calcFiles[index]);
                $scope.calcFiles[index] = data.response;
                setGroupProperties(groupProperties, index);

                $scope.setPagination($scope.calcFilesCurrentPage);
            });
        };

        $scope.setImageSepia = function (file) {
            CalcFileService.setImageSepia(file.ID).then(function (data) {
                console.log(data);
                var index = _.findIndex($scope.calcFiles, {ID: file.ID});
                if (index === -1) {
                    return true;
                }

                var groupProperties = copyGroupProperties($scope.calcFiles[index]);
                $scope.calcFiles[index] = data.response;
                setGroupProperties(groupProperties, index);

                $scope.setPagination($scope.calcFilesCurrentPage);
            });
        };

        $scope.allFilesToBW = function () {
            $scope.calcFilesLoading.isBW = true;
            CalcFileService.setCollectionToBW($scope.calcFilesSetID).then(function (data) {
                console.log(data);
                $scope.calcFiles = data.calcFiles;
                $scope.calcFilesLoading.isBW = false;
                $scope.setPagination($scope.calcFilesCurrentPage);
            });
        };

        $scope.allFilesToSepia = function () {
            $scope.calcFilesLoading.isSepia = true;
            CalcFileService.setCollectionToSepia($scope.calcFilesSetID).then(function (data) {
                console.log(data);
                $scope.calcFiles = data.calcFiles;
                $scope.calcFilesLoading.isSepia = false;
                $scope.setPagination($scope.calcFilesCurrentPage);
            });
        };

        $scope.allFilesRemoveFilters = function () {
            $scope.calcFilesLoading.removeFilters = true;
            CalcFileService.removeCollectionFilters($scope.calcFilesSetID).then(function (data) {
                console.log(data);
                $scope.calcFiles = data.calcFiles;
                $scope.calcFilesLoading.removeFilters = false;
                $scope.setPagination($scope.calcFilesCurrentPage);
            });
        };

        $scope.restoreAllImages = function () {
            $scope.calcFilesLoading.restoreAllImages = true;
            CalcFileService.removeCollectionFilters($scope.calcFilesSetID).then(function (data) {
                console.log(data);
                $scope.calcFiles = data.calcFiles;
                $scope.calcFilesLoading.removeFilters = false;
                $scope.setPagination($scope.calcFilesCurrentPage);
            });
        };

        $scope.setPagination = function (page) {
            $scope.calcFilesCurrentPage = page;
            var indexFrom = $scope.calcFilesPerPage * (page - 1);
            var indexTo = indexFrom + $scope.calcFilesPerPage;
            $scope.calcFilesDisplay = _.slice($scope.calcFiles, indexFrom, indexTo);
        }

        $scope.setPerPage = function (perPage) {
            $scope.calcFilesPerPage = perPage;
            $scope.setPagination(1);
        }

        $scope.scrollProduct = function (dir) {
            // Filtrowanie typów, aby wykluczyć elementy z isEditor
            var types = _.filter($rootScope.allTypes, function(item) { return !item.isEditor; });

            // Znajdź indeks aktualnego typu
            var idx = _.findIndex(types, { name: $scope.currentType.name });

            // Sprawdzenie, czy znaleziono typ
            if (idx === -1) return; // Bezpieczne wyjście, jeśli nie znaleziono typu

            // Przechowanie długości tablicy w zmiennej lokalnej dla optymalizacji
            var totalTypes = types.length;

            // Zmienna dla nowego indeksu
            var newIndex;

            // Zmiana indeksu w zależności od kierunku
            if (dir === 1) {
                newIndex = (idx + 1) % totalTypes;
            } else if (dir === -1) {
                newIndex = (idx === 0) ? totalTypes - 1 : idx - 1;
            } else {
                return; // Bezpieczne wyjście, jeśli kierunek jest nieprawidłowy
            }

            // Pobierz nowy typ produktu na podstawie nowego indeksu
            var type = types[newIndex];

            // Wywołaj funkcję wybierającą nowy typ
            $scope.selectType(type);
        }


        $scope.restoreImage = function (file) {
            console.log('restoreImage');
            CalcFileService.restoreImage(file.ID).then(function (data) {
                console.log(data);
                if (data.success) {
                    var index = _.findIndex($scope.calcFiles, {ID: file.ID});
                    if (index === -1) {
                        return true;
                    }

                    var groupProperties = copyGroupProperties($scope.calcFiles[index]);
                    $scope.calcFiles[index] = data.response;
                    setGroupProperties(groupProperties, index);

                    $scope.setPagination($scope.calcFilesCurrentPage);
                }
            });
        };

        $scope.modifyImage = function (image) {
            console.log(image);
            $modal.open({
                scope: $scope,
                size: 'lg',
                backdrop: true,
                controller: function ($scope, $modalInstance) {
                    var calcFile = image;
                    var cropper;
                    var img;
                    var canvas;
                    var croppedData;
                    var editImageData = JSON.parse(calcFile.editData);

                    $timeout(function () {
                        var imageURL = image.isCropped == 1 ? image.originalUrl : image.url;
                        img = new Image();
                        canvas = document.getElementById("canvas");
                        var ctx = canvas.getContext("2d");
                        img = new Image();
                        img.src = imageURL + '?' + new Date().getTime();
                        img.setAttribute('crossOrigin', '');
                        img.onload = function () {
                            canvas.width = img.width;
                            canvas.height = img.height;
                            ctx.drawImage(img, 0, 0, img.width, img.height);
                        };

                        croppedData = calcFile.isCropped == 1 ? JSON.parse(calcFile.cropData) : {};
                        $scope.imageQuality = $scope.checkImageQuality(calcFile.width, calcFile.height);

                        $timeout(function () {
                            cropper = new Cropper(canvas, {
                                data: croppedData,
                                autoCrop: true,
                                aspectRatio: $scope.complexProducts[0].selectedProduct.data.currentFormat.width / $scope.complexProducts[0].selectedProduct.data.currentFormat.height,
                                crop(event) {
                                    $scope.imageQuality = $scope.checkImageQuality(event.detail.width, event.detail.height);
                                },
                            });
                            canvas.style.display = 'block';
                        }, 500);

                        $timeout(function () {
                            var cropData = cropper.getData();
                            $scope.imageQuality = $scope.checkImageQuality(Math.ceil(cropData.width), Math.ceil(cropData.height));
                        }, 500);

                    }, 500);

                    $scope.send = function () {
                        var cropData = cropper.getData();
                        cropData.json = JSON.stringify(cropData);
                        CalcFileService.cropImage(calcFile.ID, cropData).then(function (data) {
                            if (data.success) {
                                console.log('cropImage');
                                console.log(data);
                                CalcFileService.editImage(calcFile.ID, editImageData).then(function (editData) {
                                    if (editData.success) {
                                        console.log('editImage');
                                        console.log(editData);

                                        var index = _.findIndex($scope.calcFiles, {ID: calcFile.ID});
                                        if (index === -1) {
                                            return true;
                                        }

                                        var groupProperties = copyGroupProperties($scope.calcFiles[index]);
                                        $scope.calcFiles[index] = editData.file;
                                        setGroupProperties(groupProperties, index);

                                        $scope.setPagination($scope.calcFilesCurrentPage);
                                    }
                                    $modalInstance.close();
                                });
                            }
                        });
                    };
                },
                template: '<div class="modal-header">\n' +
                    '    <h4 class="modal-title">{{"crop_an_image" |translate }}</h4>\n' +
                    '    <h5 ng-if="!imageQuality.isCorrect" style="color: red;"><i class="fa fa-warning"></i> <b>{{"bad_image_quality" | translate }}</b></h5>\n' +
                    '    <p ng-if="!imageQuality.isCorrect">{{"image_must_be_at_least" | translate }} {{imageQuality.pixelSize.width}}px x {{imageQuality.pixelSize.height}}px</p>\n' +
                    '</div>\n' +
                    '<div class="modal-body">\n' +
                    '    <div class="row">\n' +
                    '      <canvas id="canvas" style="display: none; width: 100%; height: auto;"></canvas>\n' +
                    '    </div>\n' +
                    '</div>\n' +
                    '<div class="modal-footer">\n' +
                    '    <button class="btn btn-default" ng-click="$dismiss()">{{ \'cancel\' | translate }}</button>\n' +
                    '    <button class="btn btn-success" ng-click="send()"><i class="fa fa-check"></i> {{ \'submit\' | translate }}</button>\n' +
                    '</div>'
            })
        }

        $scope.copyImage = function (file) {
            CalcFileService.copyImage(file.ID).then(function (data) {
                console.log(data);
                if (data.success) {
                    var newFile = data.response;
                    var copyOf = file.copyOf;
                    var searchFileID = file.ID;
                    if (copyOf != 0) {
                        searchFileID = file.copyOf;
                    }
                    var index = _.findIndex($scope.calcFiles, {ID: searchFileID});
                    if (index === -1) {
                        return true;
                    }

                    if (!$scope.calcFiles[index].copies || $scope.calcFiles[index].copies == 0) {
                        $scope.calcFiles[index].copies = 1;
                        $scope.calcFiles[index].isFirstInGroup = true;
                        $scope.calcFiles[index].isLastInGroup = false;
                        newFile.isFirstInGroup = false;
                        newFile.isLastInGroup = true;
                    } else {
                        $scope.calcFiles[index].copies += 1;
                        newFile.isFirstInGroup = false;
                        newFile.isLastInGroup = false;
                    }
                    newFile.copies = 0;

                    $scope.calcFiles.splice(index + 1, 0, newFile);
                    $scope.setNewVolume(caclulateCalcFilesVolume());
                    $scope.setPagination($scope.calcFilesCurrentPage);
                }
            });
        }

        var timerId;
        $scope.changeQty = function (file, type) {
            if (file.qty == 1 && type == 'minus') {
                Notification.error($filter('translate')('cannot_order_less_than_one'));
                return;
            }

            var newQty = file.qty;
            if (type == 'plus') {
                newQty++;
            } else if (type == 'minus') {
                newQty--;
            }
            var sendData = {newQty};
            CalcFileService.changeQty(file.ID, sendData).then(function (data) {
                if (data.success) {
                    file.qty = data.file.qty;
                    clearTimeout(timerId);
                    timerId = setTimeout(function () {
                        $scope.setNewVolume(caclulateCalcFilesVolume());
                    }, 1000);
                }
            });
        }

        $scope.checkImageQuality = function (width, height) {
            width = Math.ceil(width);
            height = Math.ceil(height);
            var isCorrect = true;
            var pixelSize = getPixelSizes($scope.complexProducts[0].selectedProduct.data.currentFormat);
            if (width < pixelSize.width || height < pixelSize.height) {
                isCorrect = false;
            }

            return {isCorrect, pixelSize};
        }

        function caclulateCalcFilesVolume() {
            var sum = 0;
            _.each($scope.calcFiles, function (calcFile) {
                sum += calcFile.qty;
            });

            return sum;
        }

        function getPixelSizes(format) {
            /* Dla maszyn o rozdzielczości 300 dpi
            9 x 13 8,9 x 12,7 cm 1051 x 1500 pikseli
            10 x 15 10,2 x 15,2 cm 1205 x 1795 pikseli
            13 x 18 12,7 x 17,8 cm 1500 x 2102 pikseli
            15 x 21 15,2 x 21,0 cm 1795 x 2480 pikseli
            21 x 30 21,0 x 30,0 cm 2480 x 3543 pikseli
            */
            var returnSizes = {width: 0, height: 0};
            if (format.height == 89 && format.width == 127) {
                returnSizes.height = 1051;
                returnSizes.width = 1500;
            } else if (format.height == 102 && format.width == 152) {
                returnSizes.height = 1205;
                returnSizes.width = 1795;
            } else if (format.height == 127 && format.width == 178) {
                returnSizes.height = 1500;
                returnSizes.width = 2102;
            } else if (format.height == 152 && format.width == 210) {
                returnSizes.height = 1795;
                returnSizes.width = 2480;
            } else if (format.height == 210 && format.width == 300) {
                returnSizes.height = 2480;
                returnSizes.width = 3543;
            }

            return returnSizes;
        }

        $scope.insertHtml = function(string) {
            return $sce.trustAsHtml(string);
        };

        $scope.editImage = function (image) {
            console.log('editImage');
            console.log(image);
            $scope.editButtons = {brightness: 0, contrast: 0};
            $scope.editImageData = {brightness: 0, contrast: 0};
            $modal.open({
                scope: $scope,
                size: 'lg',
                backdrop: true,
                controller: function ($scope, $modalInstance) {
                    var calcFile = image;
                    $scope.imageQuality = $scope.checkImageQuality(calcFile.width, calcFile.height);
                    var img;
                    var canvas;
                    var ctx;
                    var imageURL = image.isCropped == 1 ? image.originalCroppedUrl : image.originalUrl;

                    function generateNewOriginalImage() {
                        img = new Image();
                        img.src = imageURL + '?' + new Date().getTime();
                        img.setAttribute('crossOrigin', '');
                        img.onload = function () {
                            canvas.width = img.width;
                            canvas.height = img.height;
                            ctx.drawImage(img, 0, 0, img.width, img.height);
                        };
                    }

                    $timeout(function () {
                        canvas = document.getElementById("canvas");
                        ctx = canvas.getContext("2d");
                        generateNewOriginalImage();

                        $timeout(function () {
                            console.log(calcFile.editData);
                            if (calcFile.editData) {
                                var parsedEditData = JSON.parse(calcFile.editData);
                                $scope.editImageData.brightness = parseInt(parsedEditData.brightness) - 100;
                                $scope.editImageData.contrast = parseInt(parsedEditData.contrast) - 100;
                                $scope.editButtons.brightness = parseInt(parsedEditData.brightness) - 100;
                                $scope.editButtons.contrast = parseInt(parsedEditData.contrast) - 100;
                                Caman("#canvas", img, function () {
                                    this.brightness($scope.editImageData.brightness);
                                    this.contrast($scope.editImageData.contrast);
                                    this.render();
                                });
                                console.log($scope.editImageData);
                            }
                        }, 200);
                    }, 500);

                    $scope.send = function () {
                        CalcFileService.editImage(calcFile.ID, $scope.editImageData).then(function (editData) {
                            console.log('editImage');
                            console.log(editData);
                            if (editData.success) {
                                var index = _.findIndex($scope.calcFiles, {ID: calcFile.ID});
                                if (index === -1) {
                                    return true;
                                }

                                var groupProperties = copyGroupProperties($scope.calcFiles[index]);
                                $scope.calcFiles[index] = editData.file;
                                setGroupProperties(groupProperties, index);

                                $scope.setPagination($scope.calcFilesCurrentPage);
                            }
                            $modalInstance.close();
                        });
                    };

                    var brightnessDebounce;
                    $scope.brightnessChange = function () {
                        clearTimeout(brightnessDebounce);
                        brightnessDebounce = setTimeout(function () {
                            $scope.editImageData.brightness = 100 + parseInt($scope.editButtons.brightness);
                            $scope.editImageData.contrast = 100 + parseInt($scope.editButtons.contrast);
                            Caman("#canvas", function () {
                                this.reset();
                                this.brightness(parseInt($scope.editButtons.brightness));
                                this.contrast(parseInt($scope.editButtons.contrast));
                                this.render();
                            });
                        }, 500);
                    };
                },
                template: '<div class="modal-header">\n' +
                    '    <h4 class="modal-title">{{"edit_an_image" |translate }}</h4>\n' +
                    '    <h5 ng-if="!imageQuality.isCorrect" style="color: red;"><i class="fa fa-warning"></i> <b>{{"bad_image_quality" | translate }}</b></h5>\n' +
                    '    <p ng-if="!imageQuality.isCorrect">{{"image_must_be_at_least" | translate }} {{imageQuality.pixelSize.width}}px x {{imageQuality.pixelSize.height}}px</p>\n' +
                    '</div>\n' +
                    '<div class="modal-body">\n' +
                    '    <div class="row editImageWrapper">\n' +
                    '       <div class="imageCol">\n' +
                    '           <canvas id="canvas" style="width: 100%; height: auto;"></canvas>\n' +
                    '       </div>\n' +
                    '       <div class="editCol">\n' +
                    '           <div class="rangeCol">\n' +
                    '               <h4>\n' +
                    '                   {{"brightness" | translate }} ({{editButtons.brightness}} %)\n' +
                    '               </h4>\n' +
                    '              <input type="range" min="-100" max="100" value="' + $scope.editButtons.brightness + '" ng-model="editButtons.brightness" ng-change="brightnessChange()"/>\n' +
                    '           </div>\n' +
                    '           <div class="rangeCol">\n' +
                    '               <h4>\n' +
                    '                   {{"contrast" | translate }} ({{editButtons.contrast}} %)\n' +
                    '               </h4>\n' +
                    '              <input type="range" min="-100" max="100" value="' + $scope.editButtons.contrast + '" ng-model="editButtons.contrast" ng-change="brightnessChange()"/>\n' +
                    '           </div>\n' +
                    '       </div>\n' +
                    '    </div>\n' +
                    '</div>\n' +
                    '<div class="modal-footer">\n' +
                    '    <button class="btn btn-default" ng-click="$dismiss()">{{ \'cancel\' | translate }}</button>\n' +
                    '    <button class="btn btn-success" ng-click="send()"><i class="fa fa-check"></i> {{ \'submit\' | translate }}</button>\n' +
                    '</div>'
            })
        }
    });

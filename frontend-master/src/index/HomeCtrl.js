'use strict';

angular.module('dpClient.app')
    .controller('index.HomeCtrl', function ($rootScope, $scope, $state, $filter, $q, UserService, AuthService,
                                            DomainService, Notification, DpCategoryService,
                                            CategoryDescriptionService, HomepageBannerService, MainWidgetService) {

        $scope.activeCategoryID = null;
        $scope.articles = [];
        $scope.startCategories = [];
        $scope.mainButtonActive = false;
        $scope._ = _;

        function init() {
            $scope.items = [];
            $scope.products = [];
            forView();
            MainWidgetService.includeTemplateVariables($scope, 'content');
        }

        $scope.itemsClassName = function(product){
            var attrIconWith = product.attributeIconWidth ? product.attributeIconWidth : $scope.attributeIconWidth;
            var iconWidth = attrIconWith === 0 ? 1 : attrIconWith;
            if (($scope.attributeDescView == 0 || $scope.attributeDescView == 3) && $scope.attributeMenuLeft == 0 && $scope.attributeIconsCount == 0){
                return 'col-xs-6 col-sm-4 col-md-'+(iconWidth*3)+' col-lg-'+(iconWidth*3);
            
            }else if (($scope.attributeDescView == 0 || $scope.attributeDescView == 3) && $scope.attributeMenuLeft == 0 && $scope.attributeIconsCount == 1){
                return 'col-xs-12 col-sm-4 col-md-2 col-lg-2 col-md-'+(iconWidth*2)+'-20pp';

            }else if (($scope.attributeDescView == 0 || $scope.attributeDescView == 3) && $scope.attributeMenuLeft == 0 && $scope.attributeIconsCount == 2){
                return 'col-xs-6 col-sm-3 col-md-'+(iconWidth*2)+' col-lg-'+(iconWidth*2);
            
            }else if (($scope.attributeDescView == 1 || $scope.attributeDescView == 2) && $scope.attributeMenuLeft == 0){
                return 'col-xs-12 col-sm-12 col-md-6 col-lg-6';

            }else if ($scope.attributeMenuLeft == 1){
                return 'col-xs-4 col-sm-4 col-md-4 col-lg-4';
            }
        }

        $scope.loadOtherTemplateVariables=function(templateName){
            MainWidgetService.includeTemplateVariables($scope, templateName, undefined, undefined, undefined, true);
        };

        $scope.getTemplateVariable=function(collection, itemType,id,variableName,defaultValue){
            return MainWidgetService.getTemplateVariable($scope, collection, itemType,id,variableName,defaultValue);
        };

        function forView() {
            DpCategoryService.forView().then(function (data) {
                $scope.items = data;
                var tmpItems = [];
                _.each($scope.items, function (item) {
                    tmpItems.push(item.ID);
                    if( item.onMainPage === 1 ) {
                        $scope.startCategories.push(item.ID);
                        $scope.mainButtonActive = true;
                    }
                });
                getProducts(tmpItems);
                getDescription(tmpItems);
                getSlider();
            }, function (data) {
                Notification.error($filter('translate')('error'));
            });
        }

        function getProducts(list) {
            $q.all([DpCategoryService.manyForView(list),
                MainWidgetService.includeTemplateVariables($scope, 'calc', undefined, undefined, undefined, true),
                MainWidgetService.includeTemplateVariables($scope, 'group', undefined, undefined, undefined, true),
                MainWidgetService.includeTemplateVariables($scope, 'category', undefined, undefined, undefined, true),
            ]).then(function (data) {
                $scope.products = data[0];
                var tplCalcVars = data[1].response[0].value;
                var tplGroupVars = data[2].response[0].value;
                var tplCategoryVars = data[3].response[0].value;//TODO

                function assignVariables(product, tplItems) {
                    _.each(tplItems, function (item) {
                        product[item.name] = item.value;
                    })

                }

                _.each($scope.products, function (productList) {
                    _.each(productList, function (product) {
                        if (product.relType === 1) {
                            var tplItems = _.filter(tplGroupVars, function (item) {
                                return item.groupID == product.ID
                            });
                            assignVariables(product, tplItems);
                        } else if (product.relType === 2) {
                            var tplItems = _.filter(tplCalcVars, function (item) {
                                return item.typeID == product.ID
                            });
                            assignVariables(product, tplItems);
                        }
                    });
                });


            }, function (errors) {
                Notification.error($filter('translate')('error'));
            });
        }

        function getDescription(list) {

            CategoryDescriptionService.getAll(list).then(function (data) {

                if (_.isEmpty(data)) {
                    return;
                }

                var idx;

                _.each(data, function (catDescriptions, cIndex) {
                    _.each(catDescriptions, function (catDesc) {

                        idx = _.findIndex($scope.items, {ID: parseInt(cIndex)});

                        switch (catDesc.descType) {

                            case 1:
                                if ($scope.items[idx] !== undefined) {
                                    if ($scope.items[idx].descriptions === undefined) {
                                        $scope.items[idx].descriptions = [];
                                    }
                                    $scope.items[idx].descriptions.push(catDesc);
                                }
                                break;
                            case 5:
                                if ($scope.items[idx] !== undefined) {
                                    if ($scope.items[idx].galleries === undefined) {
                                        $scope.items[idx].galleries = [];
                                    }

                                    catDesc.items = [];

                                    if (!_.isEmpty(catDesc.files)) {
                                        _.each(catDesc.files, function (oneFile) {
                                            catDesc.items.push({
                                                thumb: oneFile.urlCrop,
                                                img: oneFile.url,
                                                description: 'Image ' + oneFile.fileID
                                            });
                                        });
                                    }
                                    $scope.items[idx].galleries.push(catDesc);
                                }
                                break;
                        }

                    });

                });

            });

        }

        function getSlider() {

            HomepageBannerService.getAll().then(function (data) {
                var sliderData = [];
                sliderData.push({'ID': 1, 'files': data});
                $rootScope.$emit('Slider:data', sliderData);
            });

        }

        $scope.setActiveCategory = function (item) {
            $scope.activeCategoryID = item.ID;
            $scope.mainButtonActive = false;
        };

        $scope.setActiveMainButton = function() {
            $scope.mainButtonActive = true;
            $scope.activeCategoryID = null;
        };

        init();

    });

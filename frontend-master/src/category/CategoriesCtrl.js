'use strict';

angular.module('dpClient.app')
    .controller('category.CategoriesCtrl', function ($scope, $q, $rootScope, $filter, DpCategoryService, $stateParams,
                                                     Notification, SubCategoryDescriptionService, MainWidgetService) {

        var currentCategoryUrl;

        $scope.descriptions = [];
        $scope.galleries = [];
        $scope.subCategories = [];


        function init() {

            $scope.items = [];
            $scope.form = {};
            $scope.groups = [];
            $scope.category = {};
            currentCategoryUrl = $scope.currentCategoryUrl = $stateParams.categoryurl;
            getContains(currentCategoryUrl);
            getOne(currentCategoryUrl).then(function (cat) {
                getDescription(currentCategoryUrl);
                MainWidgetService.includeTemplateVariables($scope, 'category', undefined, undefined, cat.ID);
            });

            getChilds(currentCategoryUrl).then( function(subCategories) {
                $scope.subCategories = subCategories;
            });

        }

        init();

        function getContains(currentCategoryUrl) {
            $q.all([DpCategoryService.getContains(currentCategoryUrl), MainWidgetService.includeTemplateVariables($scope, 'group', undefined, undefined, undefined, true)]).then(function (data) {
                $scope.items = data[0];
                var tplVars = data[1].response[0].value;
                _.each(tplVars, function (tplVar) {
                    if (tplVar.groupID) {
                        var groupItem = _.find($scope.items, {itemID: tplVar.groupID});
                        if (groupItem) {
                            groupItem[tplVar.name] = tplVar.value;
                        }
                    }
                });
            }, function (errors) {
                Notification.error($filter('translate')('error'));
            });
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

        function getOne(currentCategoryUrl) {
            var def = $q.defer();

            DpCategoryService.getOneForView(currentCategoryUrl).then(function (data) {
                $scope.category = data;
                if( $rootScope.currentLang && $rootScope.currentLang.code && data.langs ) {
                    $rootScope.customBreadcrumbs.category = data.langs[$rootScope.currentLang.code].name;
                } else {
                    $rootScope.customBreadcrumbs.category = $filter('translate')('category');
                }
                def.resolve(data);
            }, function (data) {
                Notification.error($filter('translate')('error'));
            });

            return def.promise;
        }

        function getDescription(currentCategoryUrl) {

            SubCategoryDescriptionService.getAll(currentCategoryUrl).then(function (data) {

                var sliderData = [];

                if (!_.isEmpty(data)) {

                    _.each(data, function (oneDesc) {

                        switch (oneDesc.descType) {
                            case 1:
                                $scope.descriptions.push(oneDesc);
                                break;
                            case 5:

                                oneDesc.items = [];

                                if (!_.isEmpty(oneDesc.files)) {
                                    _.each(oneDesc.files, function (oneFile) {
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

                                //$scope.thumbnails.push(oneDesc);

                                break;
                        }

                    });

                }

                $rootScope.$emit('Slider:data', sliderData);

            });
        }

        function getChilds( currentCategoryUrl ) {
            var def = $q.defer();

            DpCategoryService.getChilds(currentCategoryUrl).then(function (data) {
                $scope.subcategories = data;
                def.resolve(data);
            }, function (data) {
                Notification.error($filter('translate')('error'));
            });

            return def.promise;
        }

    });

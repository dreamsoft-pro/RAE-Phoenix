'use strict';

angular.module('dpClient.app')
	.controller('category.GroupsCtrl', function($scope, $rootScope, $filter, $q, PsTypeService, PsGroupService,
                                                DpCategoryService, PsGroupDescriptionService, $stateParams,
                                                Notification, MainWidgetService) {

	var currentGroupID;
	var currentGroupUrl;

    $scope.descriptions = [];
    $scope.galleries = [];

    function init() {
        $scope.items = [];
        $scope.group = {};
        $scope.category = {};
        $scope.form = {};
        currentGroupUrl = $scope.currentGroupUrl = $stateParams.groupurl;
        getTypes(currentGroupUrl);
        getGroup(currentGroupUrl);
        getOne( $stateParams.categoryurl );
        getDescription( currentGroupUrl );
    }

    init();

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

        function getTypes(currentGroupUrl) {
            $q.all([PsTypeService.forView(currentGroupUrl), MainWidgetService.includeTemplateVariables($scope, 'calc', undefined, undefined, undefined, true)]).then(function (data) {
                $scope.items = data[0];
                var tplVars = data[1].response[0].value;
                _.each(tplVars, function (tplVar) {
                    if (tplVar.typeID) {
                        var typeItem = _.find($scope.items, {ID: tplVar.typeID});
                        if (typeItem) {
                            typeItem[tplVar.name] = tplVar.value;
                        }
                    }
                });
            }, function (errors) {
                Notification.error($filter('translate')('error'));
            });
        }

    function getGroup( currentGroupUrl ) {
        PsGroupService.getOneForView( currentGroupUrl ).then(function(data) {
            $scope.group = data;
            if( $rootScope.currentLang && $rootScope.currentLang.code ) {
                $rootScope.customBreadcrumbs.group = data.names[$rootScope.currentLang.code];
            } else {
                $rootScope.customBreadcrumbs.group = $filter('translate')('group');
            }
            MainWidgetService.includeTemplateVariables($scope, 'group', data.ID);
        }, function(data) {
            Notification.error($filter('translate')('error'));
        });
    }

    function getOne(currentCategoryUrl) {
        DpCategoryService.getOneForView(currentCategoryUrl).then(function (data) {
            $scope.category = data;
            if( $rootScope.currentLang && $rootScope.currentLang.code && data.langs ) {
                $rootScope.customBreadcrumbs.category = data.langs[$rootScope.currentLang.code].name;
            } else {
                $rootScope.customBreadcrumbs.category = $filter('translate')('category');
            }
        }, function (data) {
            Notification.error($filter('translate')('error'));
        });
    }

    function getDescription( groupUrl ) {

        PsGroupDescriptionService.getAll(groupUrl).then(function (data) {

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

});

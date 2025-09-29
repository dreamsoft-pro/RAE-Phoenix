'use strict';

angular.module('dpClient.app')
    .controller('client-zone.QuestionsCtrl', function ($scope, ClientZoneWidgetService, $timeout, ApiCollection ) {

        $scope.pagingSettings = ClientZoneWidgetService.getPagingSettings();
        $scope.pageSizeSelect = ClientZoneWidgetService.getPageSizeSelect();

        $scope.offerFilters = {
            dateFrom: null,
            dateTo: null,
            text: null
        };

        var timerId;

        function init() {
            $scope.customProductConfig = {
                count: 'dp_customProducts/publicCount',
                params: {
                    limit: $scope.pagingSettings.pageSize
                },
                onSuccess: function (data) {
                    $scope.customProductsCtrl.items = [];
                    _.each(data, function(offer, index) {
                        offer.isCollapsed = true;
                        offer.contentArray = offer.content.split('\n');
                        $scope.customProductsCtrl.items.push(offer);
                    });

                    $scope.pagingSettings.total = data.count;
                }
            };

            $scope.customProductsCtrl = new ApiCollection('dp_customProducts/getPublic', $scope.customProductConfig);

            $scope.customProductsCtrl.get();

            var updateTableTimeout;

            $scope.setParams = function () {
                $timeout.cancel(updateTableTimeout);
                updateTableTimeout = $timeout(function () {
                    $scope.customProductsCtrl.get();
                }, 600);
            };
        }

        $scope.filterOffersDate = function(){
            if($scope.offerFilters.dateFrom && $scope.offerFilters.dateTo){
                $scope.customProductsCtrl.params.dateFrom = ($scope.offerFilters.dateFrom.getTime()/1000);
                $scope.customProductsCtrl.params.dateTo = (($scope.offerFilters.dateTo.getTime()/1000)+(60*60*24));
                $scope.setParams();
            }
         }

         $scope.clearFilters = function(){
            $scope.customProductsCtrl.params.dateFrom = null;
            $scope.customProductsCtrl.params.dateTo = null;
            $scope.offerFilters = {
                dateFrom: null,
                dateTo: null
            };
            $scope.setParams();
         }

        $scope.filterOffersText = function () {
            clearTimeout(timerId);
            timerId = setTimeout(function () {
                $scope.customProductsCtrl.params.ID = $scope.offerFilters.text;
                $scope.setParams();
            }, 500);
        };

        $scope.changeLimit = function (newLimit) {
            $scope.pagingSettings.pageSize = newLimit;
            $scope.customProductsCtrl.params.limit = $scope.pagingSettings.pageSize;
            $scope.getNextPage(1);
        };

        $scope.getNextPage = function (page) {
            $scope.pagingSettings.currentPage = page;
            $scope.customProductsCtrl.params.offset = ($scope.pagingSettings.currentPage - 1) * $scope.pagingSettings.pageSize;
            $scope.setParams();
        };

        init();

    });

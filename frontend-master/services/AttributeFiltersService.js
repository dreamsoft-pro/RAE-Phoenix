angular.module('digitalprint.services')
    .factory('AttributeFiltersService', function ($config, $q, $http) {

        var AttributeFiltersService = {};
        AttributeFiltersService.getAttributeFilters = function (attrID) {
            var def = $q.defer();

            $http({
                method: 'GET',
                url: $config.API_URL + ['attributeFilters', attrID].join('/')
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        AttributeFiltersService.getProductsUsingOptions = function (attrID) {
            var def = $q.defer();

            $http({
                method: 'GET',
                url: $config.API_URL + ['productsUsingOptions', attrID].join('/')
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        AttributeFiltersService.getOptions = function (attrID) {
            var def = $q.defer();

            $http({
                method: 'GET',
                url: $config.API_URL + ['attributeOptions', attrID].join('/')
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        AttributeFiltersService.getOption = function (data) {
            var def = $q.defer();

            $http({
                method: 'POST',
                url: $config.API_URL + 'attributeOption',
                data: data
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        AttributeFiltersService.getRelativePapers = function (data) {
            var def = $q.defer();

            $http({
                method: 'POST',
                url: $config.API_URL + 'getRelativePapers',
                data: data
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        AttributeFiltersService.search = function (attrID, filter) {
            var def = $q.defer();
            $http({
                method: 'POST',
                url: $config.API_URL + ['attributeFilters', attrID].join('/'),
                data: filter
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        AttributeFiltersService.downloadPDF = function (data) {
            var def = $q.defer();

            $http({
                method: 'POST',
                url: $config.API_URL + ['attributeOptionPDF', data.optID].join('/'),
                data: data
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        return AttributeFiltersService;

    });

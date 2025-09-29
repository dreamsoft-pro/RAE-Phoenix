angular.module('digitalprint.services')
    .factory('DpCartsDataService', function ($q, $http, $config) {

        var DpCartsDataService = {};

        var resource = 'dp_carts_data';

        DpCartsDataService.get = function (id) {
            var def = $q.defer();
            $http({
                method: 'GET',
                url: $config.API_URL + [resource, id].join('/')
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        DpCartsDataService.add = function (carts) {
            var def = $q.defer();
            $http({
                method: 'POST',
                url: $config.API_URL + [resource].join('/'),
                data: carts
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        DpCartsDataService.update = function (data) {
            var def = $q.defer();
            $http({
                method: 'POST',
                url: $config.API_URL + [resource, 'updateAddresses'].join('/'),
                data: data
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        DpCartsDataService.updateCart = function (data) {
            var def = $q.defer();
            $http({
                method: 'PATCH',
                url: $config.API_URL + [resource, 'updateAddresses'].join('/'),
                data: data
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        return DpCartsDataService;

    });

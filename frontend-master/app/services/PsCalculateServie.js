'use strict';

angular.module('digitalprint.services')
    .factory('PsCalculateService', function ($q, $http, $config, $cacheFactory) {

        var cache = $cacheFactory('ps_calculate');

        var CalculateService = function (groupID, typeID) {
            this.groupID = groupID;
            this.typeID = typeID;
            this.resource = `ps_groups/${groupID}/ps_types/${typeID}/ps_calculate`;
        };

        CalculateService.prototype.request = function (method, endpoint, data) {
            var def = $q.defer();
            var url = `${$config.API_URL}${this.resource}${endpoint ? '/' + endpoint : ''}`;

            $http({
                method: method,
                url: url,
                data: data
            }).then(function (response) {
                if (response.data.response) {
                    def.resolve(response.data);
                } else {
                    def.reject(response.data);
                }
            }, function (error) {
                def.reject(error.data);
            });

            return def.promise;
        };

        CalculateService.prototype.calculate = function (item) {
            return this.request('POST', '', item);
        };

        CalculateService.prototype.getVolumes = function (item) {
            return this.request('PATCH', '', item);
        };

        CalculateService.prototype.saveCalculation = function (preparedProduct) {
            return this.request('POST', 'saveCalculation', preparedProduct);
        };

        return CalculateService;
    });

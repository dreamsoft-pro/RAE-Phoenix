angular.module('digitalprint.services')
    .factory('LangSettingsService', function ($rootScope, $q, $http, $config, $cacheFactory) {

        var LangSettingsService = {};

        var resource = 'langsettings';

        var cache = $cacheFactory(resource);

        var getAllDef = null;

        LangSettingsService.getAll = function (force) {
            if (_.isNull(getAllDef) || force || getAllDef.promise.$$state.status === 1) {
                getAllDef = $q.defer();
            } else {
                return getAllDef.promise;
            }
            // var def = $q.defer();

            if (cache.get('collection') && !force) {
                var data=cache.get('collection')
                $rootScope.$emit('LangSettings.getAll', data);
                getAllDef.resolve(data);
            } else {
                $http({
                    method: 'GET',
                    url: $config.API_URL + resource
                }).success(function (data) {
                    cache.put('collection', data);
                    $rootScope.$emit('LangSettings.getAll', data);
                    getAllDef.resolve(data);
                }).error(function (data) {
                    getAllDef.reject(data);
                });
            }

            return getAllDef.promise;
        };

        LangSettingsService.create = function (lang) {
            var def = $q.defer();

            $http({
                method: 'POST',
                url: $config.API_URL + resource,
                data: lang
            }).success(function (data) {
                if (data.ID) {
                    cache.remove('collection');
                    def.resolve(data);
                } else {
                    def.reject(data);
                }
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        LangSettingsService.update = function (lang) {
            var def = $q.defer();

            $http({
                method: 'PUT',
                url: $config.API_URL + resource,
                data: lang
            }).success(function (data) {
                if (data.response) {
                    def.resolve(data);
                } else {
                    def.reject(data);
                }
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        LangSettingsService.remove = function (id) {
            var def = $q.defer();

            $http({
                method: 'DELETE',
                url: $config.API_URL + [resource, id].join("/")
            }).success(function (data) {
                if (data.response) {
                    def.resolve(data);
                } else {
                    def.reject(data);
                }
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        return LangSettingsService;
    });

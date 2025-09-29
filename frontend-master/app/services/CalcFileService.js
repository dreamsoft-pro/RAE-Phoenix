angular.module('digitalprint.services')
    .service('CalcFileService', function ($q, Restangular, $http, $config) {

        var CalcFileService = {};

        var resource = ['dp_products', 'calcFilesUploader'].join('/');

        CalcFileService.getUrl = function (typeID) {
            return $config.API_URL + ['dp_products', typeID, 'calcFilesUploader'].join('/');
        };


        CalcFileService.getAllByType = function (typeID) {
            var def = $q.defer();

            $http({
                method: 'GET',
                url: this.getUrl(typeID)
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        CalcFileService.removeFile = function (typeID, fileID) {
            var def = $q.defer();

            $http({
                method: 'DELETE',
                url: this.getUrl(typeID) + '/' + fileID
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };


        CalcFileService.getBySetID = function (setID) {
            var def = $q.defer();
            $http({
                method: 'GET',
                url: $config.API_URL + ['dp_products', setID, 'calcFilesUploaderSet'].join('/')
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        CalcFileService.createGuestSet = function (typeID) {
            var def = $q.defer();
            $http({
                method: 'GET',
                url: $config.API_URL + ['dp_products', typeID, 'calcFilesUploaderGuestSet'].join('/')
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        CalcFileService.setImageBW = function (fileID) {
            var def = $q.defer();
            $http({
                method: 'POST',
                url: $config.API_URL + ['calcFilesUploader', 'setImageBW', fileID].join('/')
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        CalcFileService.setImageSepia = function (fileID) {
            var def = $q.defer();
            $http({
                method: 'POST',
                url: $config.API_URL + ['calcFilesUploader', 'setImageSepia', fileID].join('/')
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        CalcFileService.setCollectionToBW = function (setID) {
            var def = $q.defer();
            $http({
                method: 'POST',
                url: $config.API_URL + ['calcFilesUploader', 'setCollectionToBW', setID].join('/')
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        CalcFileService.setCollectionToSepia = function (setID) {
            var def = $q.defer();
            $http({
                method: 'POST',
                url: $config.API_URL + ['calcFilesUploader', 'setCollectionToSepia', setID].join('/')
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        CalcFileService.removeCollectionFilters = function (setID) {
            var def = $q.defer();
            $http({
                method: 'POST',
                url: $config.API_URL + ['calcFilesUploader', 'removeCollectionFilters', setID].join('/')
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        CalcFileService.cropImage = function (fileID, data) {
            var def = $q.defer();
            $http({
                method: 'POST',
                url: $config.API_URL + ['calcFilesUploader', 'cropImage', fileID].join('/'),
                data
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        CalcFileService.restoreImage = function (fileID) {
            var def = $q.defer();
            $http({
                method: 'POST',
                url: $config.API_URL + ['calcFilesUploader', 'restoreImage', fileID].join('/')
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        CalcFileService.copyImage = function (fileID) {
            var def = $q.defer();
            $http({
                method: 'POST',
                url: $config.API_URL + ['calcFilesUploader', 'copyImage', fileID].join('/')
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        CalcFileService.changeQty = function (fileID, data) {
            var def = $q.defer();
            $http({
                method: 'PATCH',
                url: $config.API_URL + ['calcFilesUploader', 'changeQty', fileID].join('/'),
                data
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        CalcFileService.editImage = function (fileID, data) {
            var def = $q.defer();
            $http({
                method: 'POST',
                url: $config.API_URL + ['calcFilesUploader', 'editImage', fileID].join('/'),
                data
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        return CalcFileService;

    });

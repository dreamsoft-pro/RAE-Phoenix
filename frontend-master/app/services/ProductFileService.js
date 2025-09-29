angular.module('digitalprint.services')
    .service('ProductFileService', function ($q, Restangular, $http, $config) {

        var ProductFileService = {};

        ProductFileService.getUrl = function (productID) {
            return $config.API_URL + ['dp_products', productID, 'productFiles'].join('/');
        };

        ProductFileService.getUploadUrl = function (productID, attrID) {
            return $config.API_URL + ['dp_products', productID, 'productFiles', attrID].join('/');
        };

        ProductFileService.fixFileDimensions= (productID, fileID) => {
            var def = $q.defer();

            $http({
                method: 'PUT',
                url: ProductFileService.getUploadUrl(productID, fileID)
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        ProductFileService.saveFileProps= (productID, fileID, data) => {
            var def = $q.defer();

            $http({
                method: 'POST',
                url: $config.API_URL + ['dp_products', productID, 'productFiles', 'saveFileProps', fileID].join('/') ,
                data

            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        ProductFileService.saveProductProps= (productID, sendToFix) => {
            var def = $q.defer();

            $http({
                method: 'POST',
                url: $config.API_URL + ['dp_products', productID, 'productFiles', 'saveProductProps'].join('/') ,
                data:{sendToFix}

            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        ProductFileService.acceptFile= (productID, fileID) => {
            var def = $q.defer();

            $http({
                method: 'PATCH',
                url: ProductFileService.getUploadUrl(productID, fileID)
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        ProductFileService.getAll = function (productID) {
            var def = $q.defer();

            $http({
                method: 'GET',
                url: this.getUrl(productID)
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        ProductFileService.getByList = function(orders){
            var def = $q.defer();

            $http({
                method: 'GET',
                url: $config.API_URL + ['productFiles', 'productListFiles', orders.join(',')].join('/')
            }).success(function(data) {
                def.resolve(data);
            }).error(function(data) {
                def.reject(data);
            });

            return def.promise;
        };

        ProductFileService.removeFile = function (productID, fileID) {
            var def = $q.defer();

            $http({
                method: 'DELETE',
                url: this.getUrl(productID) + '/' + fileID
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        ProductFileService.makeMiniature = function(fileID){
            var def = $q.defer();

            $http({
                method: 'GET',
                url: $config.API_URL + ['productFiles', 'makeMiniature', fileID].join('/')
            }).success(function(data) {
                def.resolve(data);
            }).error(function(data) {
                def.reject(data);
            });

            return def.promise;
        };

        ProductFileService.acceptReport = function (productID, fileID) {
            var def = $q.defer();

            $http({
                method: 'PATCH',
                url: $config.API_URL + ['dp_products', productID, 'productFiles', fileID, 'productReportFiles'].join('/')
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        ProductFileService.rejectReport = function (productID, fileID, comment) {
            var def = $q.defer();

            $http({
                method: 'DELETE',
                url: $config.API_URL + ['dp_products', productID, 'productFiles', fileID, 'productReportFiles'].join('/'),
                data: {comment:comment},
                headers: {
                    "Content-Type": "application/json"
                }
            }).success(function (data) {
                def.resolve(data);
            }).error(function (data) {
                def.reject(data);
            });

            return def.promise;
        };

        ProductFileService.getReportsUploadUrl = function (productID, fileID) {
            return $config.API_URL + ['dp_products', productID, 'productFiles', fileID, 'productReportFiles'].join('/');
        };

        return ProductFileService;

    });

angular.module('digitalprint.services')
    .factory('LoadingService', function () {

        var loadingCount = 0;
        var errorCount = 0;
        return {
            isLoading: function () {
                return loadingCount > 0;
            },
            requested: function () {
                loadingCount++
            },
            responsed: function (status) {
                if (status != 200 && status != 401) {
                    errorCount++
                }
                loadingCount--
            },
            countError: function () {
                errorCount++
            },
            count: function () {
                return loadingCount
            },
            errorCount: function () {
                return errorCount
            }
        };
    });

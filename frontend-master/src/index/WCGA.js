angular.module('dpClient.helpers')
    .directive('wcga', function () {
        return {
            restrict: 'E',
            scope: {},
            replace: true,
            templateUrl: 'src/index/templates/wcga.html',
            controller: function ($scope, localStorageService, SettingService) {

                var Setting = new SettingService('additionalSettings');
                Setting.getPublicSettings().then(function (settingsData) {
                    $scope.wcgaUsed = settingsData.wcgaUsed.value;
                    if($scope.wcgaUsed){
                        const lsKeys = localStorageService.keys()

                        if (lsKeys.indexOf('wcgaKontrast') > -1) {
                            $('body').addClass('wcga-contrast')
                        }

                        if (lsKeys.indexOf('wcgaFonts') > -1) {
                            $('body').addClass('wcga-fonts')
                        }
                    }
                });

                $scope.changeContrast = () => {
                    $('body').toggleClass('wcga-contrast');
                    if ($('body').hasClass('wcga-contrast')) {
                        localStorageService.set('wcgaKontrast', 1)
                    } else {
                        localStorageService.remove('wcgaKontrast')
                    }
                }

                $scope.toggleFontSize = () => {
                    $('body').toggleClass('wcga-fonts')
                    if ($('body').hasClass('wcga-fonts')) {
                        localStorageService.set('wcgaFonts', 1)
                    } else {
                        localStorageService.remove('wcgaFonts')
                    }
                }

            }
        }
    })

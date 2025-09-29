angular.module('dpClient.app')
  .controller('LangCtrl', function($scope, $rootScope, $translate, $cookieStore, $window, LangSettingsService,
                                   LangSettingsRootService, Notification, $langStorage){


      $rootScope.$on('LangSettings.getAll', function (e, data) {
          var languages={}
          _.each(data, function (item) {
              if(item.active === 1) {
                  languages[item.code] = item;
              }
          });
          $rootScope.languages = languages;
      });

      LangSettingsService.getAll();

      $scope.countLanguages = function() {
          return _.values($rootScope.languages).length;
      };



      $scope.switchLanguage = function (key) {
          $rootScope.$emit('changeLang', key);
      };

      $scope.switchCurrency = function (currency) {

          var idx = _.findIndex($rootScope.currencies, {code: currency.code});

          $rootScope.currentCurrency = $scope.currentCurrency = $rootScope.currencies[idx];
          $cookieStore.put('currency', $rootScope.currentCurrency[index].code);

      };

  }).config(function($translateProvider, $langStorageProvider){
    var langArr=new Array($langStorageProvider.getLangCode());
    $translateProvider
        .fallbackLanguage(langArr)
        .registerAvailableLanguageKeys(langArr, {
            'pl_PL': 'pl',
            'en_US': 'en',
            'en_UK': 'en',
            'de_DE': 'de',
            'de_AT': 'de',
            'de_CH': 'de',
            'de_LI': 'de',
            'de_LU': 'de',
            'ru_RU': 'ru',
            'es_ES': 'es',
            'it_IT': 'it'
        })
        .useLoader('LangLoader')
        .preferredLanguage(langArr[0]);

  });

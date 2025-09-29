angular.module('dpClient.config', []);
angular.module('dpClient.routes', ['ui.router', 'restangular']);
angular.module('dpClient.directives', []);
angular.module('digitalprint.services', ['LocalStorageModule']);
angular.module('dpClient.helpers', ['ui-notification']);
angular.module('dpClient.filters', []);

angular.module('dpClient.app', [
    'LocalStorageModule',
    'ui.bootstrap',
    'pascalprecht.translate',
    'ngCookies',
    'ngAnimate',
    'angular-api-collection',
    'ui.sortable',
    'ncy-angular-breadcrumb',
    'ngSanitize',
    'textAngular',
    'btford.socket-io',
    'angularFileUpload',
    'jkuri.gallery',
    'dpClient.routes',
    'dpClient.directives',
    'digitalprint.services',
    'dpClient.helpers',
    'dpClient.filters',
    'dpClient.config',
    'bw.paging',
    'wt.responsive',
    'ngScrollbars',
    'rzModule',
    'vcRecaptcha',
    'updateMeta',
    'ngMockE2E'
])
.config(function (
    $httpProvider,
    $locationProvider,
    $urlRouterProvider,
    $stateProvider,
    RestangularProvider,
    localStorageServiceProvider,
    ApiCollectionProvider,
    $breadcrumbProvider,
    $provide,
    $configProvider
    ) {

    $configProvider.set('API_URL', 'http://localtest.me/api/');
    $configProvider.set('API_URL_EDITOR', 'http://localhost:1351/api/');
    RestangularProvider.setBaseUrl('http://localtest.me/api/');
    $configProvider.set('AUTH_URL', 'http://localtest.me:2600/');
    $configProvider.set('STATIC_URL', 'http://localtest.me/static/');
    $configProvider.set('SOCKET_URL', 'http://localtest.me:2600');
    $configProvider.set('EDITOR_URL', 'http://localhost:1400');

    function $LangStorageProvider() {
        return {
            $get: function () {
                return this;
            },
            getLangCode: () => 'pl'
        };
    }
    $provide.provider('$langStorage', $LangStorageProvider);

    $locationProvider.html5Mode(true);

    $urlRouterProvider.otherwise(function ($injector, $location) {
        // Użyj $state do przekierowania zamiast bezpośredniego zwracania URL
        $injector.get('$state').go('deliveries');
        return true; // Zwróć true, aby zatrzymać domyślne zachowanie
    });

    RestangularProvider.setMethodOverriders(['put', 'patch']);
    localStorageServiceProvider.setPrefix('digitalprint');

    $httpProvider.interceptors.push('httpMethodOverride');
    $httpProvider.interceptors.push('loadingInterceptor');
    $httpProvider.interceptors.push('responseErrorInterceptor');
})
.run(function ($q, $rootScope, $config, $state, $cookieStore, routes, getDomains, $location, Notification,
               $filter, $timeout, $urlRouter, $stateParams, AuthDataService, $window, translateRouting, LangService,
               DpOrderService, $httpBackend, $urlMatcherFactory) {
    // Tylko dla mockowania, nie używane w produkcji
    $httpBackend.whenGET(new RegExp('api\/lang\/')).respond(200, {});
    $httpBackend.whenGET(/domains/).respond(200, [{}]);
    $httpBackend.whenGET(new RegExp('api\/routes\/translateState')).respond(200, [{}]);
    $httpBackend.whenGET(new RegExp('api\/langsettings')).respond(200, [{}]);
    $httpBackend.whenGET(/\.html$/).passThrough();

    $rootScope.currentCurrency = { code: 'PLN' };

    $rootScope.routes = [];
    $rootScope.$state = $state;
    $rootScope.defaultLangCode = 'pl';

    // Inicjalizacja tras
    routes.getAll().then(function () {
        routes.setAll();
        $urlRouter.sync();
        $urlRouter.listen();
    });
})
.factory('httpMethodOverride', function () {
    return {
        request: function (config) {
            if (config.method === 'PUT' || config.method === 'PATCH') {
                config.headers['x-http-method-override'] = config.method.toLowerCase();
                config.method = 'POST';
            }
            return config;
        }
    };
})
.factory('loadingInterceptor', function ($q, $rootScope, LoadingService) {
    return {
        request: function (config) {
            LoadingService.requested();
            config.requestTimestamp = new Date().getTime();
            $rootScope.$broadcast('loading:start');
            return config;
        },
        response: function (response) {
            LoadingService.responsed();
            $rootScope.$broadcast('loading:finish');
            return response;
        },
        responseError: function (rejection) {
            if (rejection.status == 401) {
                LoadingService.responsed();
            } else {
                LoadingService.countError();
            }
            $rootScope.$broadcast('loading:finish');
            return $q.reject(rejection);
        }
    };
})
.factory('responseErrorInterceptor', function ($q, $injector, $timeout) {
    return {
        responseError: function (response) {
            console.log('responseError Status: ' + response.status);
            if (response.status == 0 || response.status == 408 || response.status >= 500) {
                var $http = $injector.get('$http');
                return $timeout(() => $http(response.config), 3000, false);
            } else {
                return $q.reject(response);
            }
        }
    };
})
.factory('routes', function ($http, $config, $q, $rootScope, $cookieStore, $stateProvider) {
    return {
        getAll: function () {
            return $http({
                url: $config.API_URL + 'routes/show',
                method: 'GET'
            })
            .then(response => {
              $rootScope.routes = response.data; // Przypisz dane do $rootScope.routes
              return response.data;
            })
            .catch(error => $q.reject(error));
        },
        setAll: function () {
          const defaultLang = $cookieStore.get('lang') ? $cookieStore.get('lang') : 'pl'; // Użyj 'pl' jako domyślnego
          const actDate = new Date();
          const dateStr = '' + actDate.getHours() + actDate.getMinutes() + actDate.getSeconds();

          // Iteruj po trasach z $rootScope.routes
          $rootScope.routes.forEach((value) => {
              value.abstract = (value.abstract == 1);

              let state;
              if (value.langs && angular.isDefined(value.langs[defaultLang]) && value.langs[defaultLang].url != null) {
                  state = {
                      name: value.name,
                      url: value.langs[defaultLang].url,
                      parent: value.parent,
                      abstract: value.abstract,
                      views: {},
                      ncyBreadcrumb: {
                          label: value.langs[defaultLang].name
                      }
                  };
              } else {
                  state = {
                      name: value.name,
                      parent: value.parent,
                      abstract: value.abstract,
                      views: {},
                      ncyBreadcrumb: { skip: true }
                  };
              }

              if (angular.isDefined(value.controller) && value.controller != null) {
                  state.controller = value.controller;
              }

              if (value.abstract === true && value.name === 'main') {
                const actTemplate = value.views.pop();
                state.templateUrl = actTemplate.template.url + '?ver=' + dateStr;
                delete state.views;
              } else if (value.route === true) {
                delete state.views;
              } else {
                angular.forEach(value.views, (view) => {
                  if (view.template) {
                    state.views[view.name] = {
                      templateUrl: view.template.url + '?ver=' + dateStr,
                      controller: view.controller
                    };
                  }
                });
              }

              $stateProvider.state(value.name, state);
          });
        },
        findOne: function (name) {
          return $q((resolve) => {
            // Szukaj trasy w $rootScope.routes
            const route = $rootScope.routes.find(each => each.name === name);
            resolve(route);
          });
        }
    };
})
.factory('getDomains', function ($q, $http, $config) {
    return {
        request: function () {
            return $http({
                url: $config.API_URL + 'domains',
                method: 'GET'
            })
            .then(res => res.data)
            .catch(err => $q.reject(new Error(err)));
        }
    };
})
.factory('translateRouting', function ($q, $rootScope, $http, $config) {
    return {
        request: function (actualState, stateParams, lang) {
            let params = { ...stateParams, lang };
            return $http({
                url: $config.API_URL + ['routes', 'translateState', actualState].join('/'),
                method: 'GET',
                params: params
            })
            .then(res => res.data)
            .catch(err => $q.reject(new Error(err)));
        }
    };
});

angular.module('dpClient.helpers').directive('initBind', function ($compile) {
    return {
        restrict: 'A',
        link: function (scope, element, attr) {
            attr.$observe('ngBindHtml', function () {
                if (attr.ngBindHtml) {
                    $compile(element[0].children)(scope);
                }
            });
        }
    };
});
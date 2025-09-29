angular.module('dpClient.config', []);
angular.module('dpClient.routes', ['ui.router', 'restangular']);
angular.module('dpClient.directives', []);
angular.module('digitalprint.services', ['LocalStorageModule']);
angular.module('dpClient.filters', []);
angular.module('dpClient.helpers', ['ui-notification']) .config(function(NotificationProvider) {
        NotificationProvider.setOptions({
            startTop: 50,
            startRight: 10,
            verticalSpacing: 20,
            horizontalSpacing: 20,
            positionX: 'right',
            positionY: 'top',
            additionalClasses: 'my-notification-class'
        });
    });
var $stateProviderRef = null;
var $urlRouterProviderRef = null;
function getLangFromUrl() {
    var path=String(location.pathname);
    var re=new RegExp('^/(.{2})/?');
    if(re.test(path)){
        return RegExp.$1;
    }
    return null;
}
function getLangFromApi() {
    var r=JSON.parse(window.globalRoutes);
    for(var k in r){
        return k; //first key if default language
    }
}
function getLangCode(){
    var fromUrl=getLangFromUrl();
    var fromApi=getLangFromApi();
    return fromUrl ? fromUrl: fromApi;
}
var $configProviderRef = null;

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
    'angular-carousel',
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
    'updateMeta'
])
    .config(function ($configProvider, $locationProvider, $urlRouterProvider, $stateProvider, RestangularProvider,
                      localStorageServiceProvider, ApiCollectionProvider, $breadcrumbProvider, $httpProvider, $provide) {

        function $LangStorageProvider() {
            return {
                $get: function () {
                    return this
                },
                getLangCode: getLangCode
            }
        }
        var reg=$provide.provider('$langStorage',$LangStorageProvider);
        $urlRouterProviderRef = $urlRouterProvider;
        $stateProviderRef = $stateProvider;
        $locationProvider.html5Mode(true);
        $urlRouterProvider.deferIntercept();

        var mainURL = 'REPLACE_API_URL';
        var staticUrlTmp = '';


        if (mainURL === 'REPLACE_API_URL') {
            $configProvider.set('API_URL', 'http://localtest.me/api/');
            $configProvider.set('API_URL_EDITOR', 'http://editor.localtest.me/api/');
            RestangularProvider.setBaseUrl('http://localtest.me/api/');
            $configProvider.set('AUTH_URL', 'http://authapp.localtest.me/');
            $configProvider.set('STATIC_URL', 'http://localtest.me/static/');
            staticUrlTmp = 'http://localtest.me/static/';
            $configProvider.set('SOCKET_URL', 'http://authapp.localtest.me');
            $configProvider.set('EDITOR_URL', 'http://editor.localtest.me');
        } else {
            $configProvider.set('API_URL', mainURL);
            RestangularProvider.setBaseUrl(mainURL);
            $configProvider.set('API_URL_EDITOR', 'REPLACE_API_URL_EDITOR');
            $configProvider.set('AUTH_URL', 'REPLACE_AUTH_URL');
            $configProvider.set('STATIC_URL', 'REPLACE_STATIC_URL');
            staticUrlTmp = 'REPLACE_STATIC_URL';
            $configProvider.set('SOCKET_URL', 'REPLACE_SOCKET_URL');
            $configProvider.set('EDITOR_URL', 'REPLACE_EDITOR_URL'+'indexu.html');
        }

        $configProvider.set('ACCESS_TOKEN_NAME', 'access-token');

        RestangularProvider.setMethodOverriders(['put', 'patch']);

        localStorageServiceProvider.setPrefix('digitalprint');

        $breadcrumbProvider.setOptions({
            includeAbstract: false,
            template: '<ol class="breadcrumb">\n' +
                '    <li ng-repeat="step in steps" ng-class="{active: $last}" ng-switch="$last || !!step.abstract">\n' +
                '        <a ng-switch-when="false" href="{{step.ncyBreadcrumbLink}}">\n' +
                '            <span ng-if="!($root.customBreadcrumbs[step.name] && $root.customBreadcrumbs[step.name] !== step.name)">\n' +
                '                {{step.ncyBreadcrumbLabel}}\n' +
                '            </span>\n' +
                '            <span ng-if="$root.customBreadcrumbs[step.name] && $root.customBreadcrumbs[step.name] !== step.name">\n' +
                '                {{ $root.customBreadcrumbs[step.name] }}\n' +
                '            </span>\n' +
                '        </a>\n' +
                '        <span ng-switch-when="true">\n' +
                '            <span ng-if="!($root.customBreadcrumbs[step.name] && $root.customBreadcrumbs[step.name] !== step.name)">\n' +
                '                {{step.ncyBreadcrumbLabel}}\n' +
                '            </span>\n' +
                '            <span ng-if="$root.customBreadcrumbs[step.name] && $root.customBreadcrumbs[step.name] !== step.name">\n' +
                '                {{ $root.customBreadcrumbs[step.name] }}\n' +
                '            </span>\n' +
                '        </span>\n' +
                '    </li>\n' +
                '</ol>'
        });

        $httpProvider.interceptors.push('authInterceptor');
        $httpProvider.interceptors.push('httpMethodOverride');
        $httpProvider.interceptors.push('loadingInterceptor');
        $httpProvider.interceptors.push('catchMailErrorInterceptor');
        $httpProvider.interceptors.push('responseErrorInterceptor');

        var blankPage = {
            abstract: false,
            templateUrl: staticUrlTmp + 'templates/default/120/404.html',
            name: 'blankPage',
            url: '/404',
            controller: function ($scope) {
                $scope.lang = getLangCode()
            }
        };
        $stateProvider.state(blankPage);
        if (window.location.pathname !== '/') {
            $urlRouterProvider.otherwise(function ($injector, $location) {
                console.error('Invalid url', $location.path())
                return '/404';
            })
        } else {
            $urlRouterProvider.otherwise(function ($injector, $location) {
                console.error('Invalid url', $location.path())
                return '/'+getLangCode();
            });
        }
        ;
        var routesContainer = JSON.parse(globalRoutes);
        var currentLang=getLangCode();
        _.each(routesContainer[currentLang], function (route) {
            $stateProvider.state(route);
        });

    })
    .run(function ($q, $rootScope, $config, $state, $cookieStore, routes, getDomains, $location, Notification,
                   $filter, $timeout, $urlRouter, $stateParams, metaTags, AuthDataService, $window, translateRouting, LangService, DpOrderService, LangSettingsService, $langStorage, DynamicCssService) {

        $rootScope.$state = $state;
        $rootScope.customBreadcrumbs = {};

        var routesContainer = JSON.parse(globalRoutes);
        var defaultLang =  getLangCode();
        $rootScope.routes = routesContainer[defaultLang];

        $configProviderRef = $config;

        getDomains.request().then(function (data) {

            _.each(data, function (oneDomain) {
                if (angular.isDefined(oneDomain.selected) && oneDomain.selected === 1) {
                    $rootScope.domainID = oneDomain.ID;
                    $rootScope.companyID = oneDomain.companyID;
                    $rootScope.STATIC_URL = $config.STATIC_URL;
                    $rootScope.domainHost = oneDomain.host;
                    $rootScope.domainName = oneDomain.name;
                    $rootScope.editorPort = oneDomain.port;
                    $rootScope.skinName = oneDomain.skinName;
                    window.googleTagManager=$rootScope.googleTagManager = oneDomain.googleTagManager;
                    $rootScope.webMasterVerifyTag = oneDomain.webMasterVerifyTag;
                    $rootScope.domainWithSsl = oneDomain.ssl;
                    $rootScope.myZoneStartPoint = oneDomain.myZoneStartPoint;
                    const statesHistory=[];
                    $rootScope.$on('$stateChangeStart', function (event, toState, toParams, fromState, fromParams) {
                        statesHistory.push({state: toState, params: toParams});
                    });
                    $rootScope.getLastFunctionalState=()=>statesHistory.reverse().find(stateData=>['login','logout'].indexOf(stateData.state.name)==-1)
                    $rootScope.currencies = [];
                    if (oneDomain.currencies.length > 0) {
                        _.each(oneDomain.currencies, function (oneCurrency) {
                            if (oneCurrency.active === 1) {
                                $rootScope.currencies.push(oneCurrency);
                            }
                        });
                    }
                    DynamicCssService.loadDomainCSS($rootScope.domainID, $rootScope.companyID);
                    _.each($rootScope.currencies, function (currency) {
                        if (angular.isDefined(currency.selected) && currency.selected === true) {

                            if ($cookieStore.get('currency')) {
                                var idx = _.findIndex($rootScope.currencies, {code: $cookieStore.get('currency')});
                                if (idx > -1) {
                                    $rootScope.currentCurrency = $rootScope.currencies[idx];
                                }
                            } else {
                                $rootScope.currentCurrency = currency;
                                $cookieStore.put('currency', currency.code);
                            }

                        }
                    });

                }
            });
            $rootScope.defaultLangCode = getLangCode();
            LangSettingsService.getAll(false).then(function (data) {
                var langCode=$langStorage.getLangCode();
                if (!$rootScope.currentLang) {
                    $rootScope.currentLang = _.find(data, {code: langCode});
                }
                $urlRouter.sync();
                $urlRouter.listen();
            });


            if ( window.location.pathname === '/' || window.location.pathname === '/' + getLangCode()) {
                $state.go('home');
            }

        }, function (data) {
            Notification.error($filter('translate')('error'));
        });
        $rootScope.$on('$stateChangeError', function(event, toState, toParams, fromState, fromParams, error){
            console.error("root change error", event, toState, toParams, fromState, fromParams, error);
        })
        $rootScope.$on('$stateChangeSuccess',
            function (event, toState, toParams, fromState, fromParams) {

                routes.findOne($state.current.name).then(function (oneRoute) {
                    metaTags.getRoute(window.location.pathname)
                        .then(function(mainTags){

                            if (document.title != mainTags.mainTagLanguage.title) {
                                document.title = mainTags.mainTagLanguage.title;
                            }

                            addMeta(mainTags.mainTagLanguage);


                            var gaScriptElement = document.getElementById('ga-script');
                            if (gaScriptElement) {
                                gaScriptElement.setAttribute('src', 'https://www.googletagmanager.com/gtag/js?id=' + mainTags.gaIdCode);
                            }


                            var faviconLinkElement = document.getElementById('favicon-link');
                            if (typeof faviconLinkElement !== "undefined" && faviconLinkElement) {
                                faviconLinkElement.setAttribute('href', mainTags.STATIC_URL + mainTags.companyID + '/images/favicon.ico');
                            }

                            var metaOgImageElement = document.getElementById('meta-og-image');
                            if (typeof metaOgImageElement !== "undefined" && metaOgImageElement) {
                                metaOgImageElement.setAttribute('content', mainTags.STATIC_URL + 'uploadedFiles/' + mainTags.companyID + 'logo');
                            }

                            window.gaIdCode = mainTags.gaIdCode;
                        });
                    if( $rootScope.urlParams === undefined ) {
                        $rootScope.urlParams = {};
                    }

                    if( !$rootScope.currentLang ) {
                        return;
                    }

                    if( !oneRoute ) {
                        return;
                    }

                    if (oneRoute.name === 'group') {

                        metaTags.getByGroup($stateParams.groupurl, $stateParams.categoryurl).then(function (metaForGroup) {
                            if (metaForGroup.response) {
                                if( metaForGroup.metaTags[$rootScope.currentLang.code] !== undefined ) {
                                    document.title = metaForGroup.metaTags[$rootScope.currentLang.code].title;
                                    addMeta(metaForGroup.metaTags[$rootScope.currentLang.code]);
                                }
                            } else {
                                if( oneRoute.metaTags ) {
                                    document.title = oneRoute.metaTags.languages[$rootScope.currentLang.code].title;
                                    addMeta(oneRoute.metaTags.languages[$rootScope.currentLang.code]);
                                } else {
                                    addHomeMeta();
                                }
                            }
                            if( metaForGroup.urlParams ) {
                                $rootScope.urlParams.group = metaForGroup.urlParams.group;
                                $rootScope.urlParams.category = metaForGroup.urlParams.category;
                            }
                        });
                    } else if (oneRoute.name === 'calculate') {
                        metaTags.getByType($stateParams.typeurl, $stateParams.categoryurl).then(function (metaForType) {

                            if (metaForType.response) {

                                if( _.isString(metaForType.metaTags[$rootScope.currentLang.code]) ) {
                                    document.title = metaForType.metaTags[$rootScope.currentLang.code].title;
                                    addMeta(metaForType.metaTags[$rootScope.currentLang.code]);
                                }
                            } else {
                                if( oneRoute.metaTags ) {
                                    document.title = oneRoute.metaTags.languages[$rootScope.currentLang.code].title;
                                    addMeta( oneRoute.metaTags.languages[$rootScope.currentLang.code] );
                                } else {
                                    addHomeMeta();
                                }
                            }
                            if( metaForType.urlParams ) {
                                $rootScope.urlParams.group = metaForType.urlParams.group;
                                $rootScope.urlParams.category = metaForType.urlParams.category;
                                $rootScope.urlParams.type = metaForType.urlParams.type;
                            }
                        });
                    } else if (oneRoute.name === 'category') {

                        metaTags.getByCategory($stateParams.categoryurl).then(function (metaForCategory) {

                            if (metaForCategory.response) {

                                if( metaForCategory.metaTags[$rootScope.currentLang.code] !== undefined ) {
                                    document.title = metaForCategory.metaTags[$rootScope.currentLang.code].title;
                                    addMeta(metaForCategory.metaTags[$rootScope.currentLang.code]);
                                }

                            } else {
                                if( oneRoute.metaTags ) {
                                    document.title = oneRoute.metaTags.languages[$rootScope.currentLang.code].title;
                                    addMeta( oneRoute.metaTags.languages[$rootScope.currentLang.code]);
                                } else {
                                    addHomeMeta();
                                }
                            }
                            if( metaForCategory.urlParams ) {
                                $rootScope.urlParams.category = metaForCategory.urlParams.category;
                            }
                        });
                    } else if (oneRoute.metaTags) {
                        document.title = oneRoute.metaTags.languages[$rootScope.currentLang.code].title;
                        addMeta( oneRoute.metaTags.languages[$rootScope.currentLang.code]);
                    } else {
                        addHomeMeta();
                    }
                });

                            function addMeta(metasource) {
                                var metaList = document.getElementsByTagName("META");

                                for (var i = 0; i < metaList.length; i++) {
                                    var content = '';
                                    if (metaList[i].name) {
                                        switch (metaList[i].name) {
                                            case 'description':
                                                content = metasource.description || '';
                                                break;
                                            case 'keywords':
                                                content = metasource.keywords || '';
                                                break;
                                            case 'og:title':
                                                content = metasource.og_title || '';
                                                break;
                                            case 'og:url':
                                                content = metasource.og_url || '';
                                                break;
                                            case 'og:site_name':
                                                content = metasource.og_site_name || '';
                                                break;
                                            case 'og:description':
                                                content = metasource.og_description || '';
                                                break;
                                            case 'og:locale':
                                                content = metasource.og_locale || '';
                                                break;
                                            case 'og:image':
                                                content = metasource.og_image || '';
                                                break;
                                            case 'og:image:secure_url':
                                                content = metasource.og_image_secure_url || '';
                                                break;
                                            case 'og:image:width':
                                                content = metasource.og_image_width || '';
                                                break;
                                            case 'og:image:height':
                                                content = metasource.og_image_height || '';
                                                break;
                                            case 'og:image:alt':
                                                content = metasource.og_image_alt || '';
                                                break;
                                            case 'twitter:card':
                                                content = metasource.twitter_card || '';
                                                break;
                                            case 'twitter:site':
                                                content = metasource.twitter_site || '';
                                                break;
                                            case 'twitter:creator':
                                                content = metasource.twitter_creator || '';
                                                break;
                                        }
                                        if (content) {
                                            metaList[i].setAttribute('content', content);
                                        }
                                    }
                                }
                            }

                function addHomeMeta() {
                    routes.findOne('home').then(function (homeRoute) {
                        if( homeRoute.metaTags !== undefined ) {
                            document.title = homeRoute.metaTags.languages[$rootScope.currentLang.code].title;
                            addMeta(homeRoute.metaTags.languages[$rootScope.currentLang.code]);
                        }
                    });
                }

                event.preventDefault();
                $("html, body").animate({
                    scrollTop: 0
                }, 600);
            });

        $rootScope.$on('changeLang', function (e, toLang) {
            translateRouting.request($state.current.name, $stateParams, toLang).then( function( data ) {
                window.location = data.urlAddress;
            });


        });

        $rootScope.$on('cartRequired', function (e,is) {
            DpOrderService.getCart().then(function(data){
                $rootScope.carts=data.carts;
                $rootScope.productCount=data.order && data.order.products ? data.order.products.length : 0;
            })
        });

    })
    .factory('httpMethodOverride', function () {
        return {
            'request': function (config) {
                if (config.method === 'PUT' || config.method === 'PATCH') {
                    config.headers['x-http-method-override'] = config.method.toLowerCase();
                    config.method = 'POST';
                }
                return config;
            }

        };
    })
    .factory('getDomains', function ($q, $http, $config) {
        return {
            request: function () {

                var def = $q.defer();

                $http({
                    url: $config.API_URL + ['domains'].join('/'),
                    method: 'GET'
                }).then(function (res) {
                    def.resolve(res.data)
                }, function (err) {
                    def.reject(new Error(err));
                });

                return def.promise;
            }
        };
    })
    .factory('translateRouting', function ($q, $rootScope, $http, $config) {
        return {
            request: function (actualState, stateParams, lang) {

                var def = $q.defer();
                var params=stateParams;
                params.lang=lang;
                $http({
                    url: $config.API_URL + ['routes', 'translateState', actualState].join('/'),
                    method: 'GET',
                    params: params
                }).then(function (res) {
                    def.resolve(res.data)
                }, function (err) {
                    def.reject(new Error(err));
                });

                return def.promise;
            }
        };
    })
    .factory('routes', function ($http, $config, $q, $rootScope, $cookieStore) {
        return {
            getAll: function () {

                var def = $q.defer();

                $http({
                    url: $config.API_URL + ['routes', 'show'].join('/'),
                    method: 'GET'
                }).then(function successCallback(response) {
                    def.resolve(response);
                }, function errorCallback(response) {
                    def.reject(response);
                });
                return def.promise;
            },
            setAll: function () {
                var def = $q.defer();

                var defaultLang = $cookieStore.get('lang') ? $cookieStore.get('lang') : getLangCode();

                var actDate = new Date();
                var dateStr = actDate.getHours() + actDate.getMinutes() + actDate.getSeconds();

                var state;

                var counter = 0;
                //this.getAll().then(function (res) {

                    _.each($rootScope.routes, function (value, index) {

                        if (value.abstract == 1) {
                            value.abstract = true;
                        } else {
                            value.abstract = false;
                        }

                        if (value.langs && angular.isDefined(value.langs[defaultLang]) && value.langs[defaultLang].url != null) {

                            state = {
                                "name": value.name,
                                "url": value.langs[defaultLang].url,
                                "parent": value.parent,
                                "abstract": value.abstract,
                                "views": {},
                                "ncyBreadcrumb": {
                                    "label": value.langs[defaultLang].name
                                }
                            };
                        } else {

                            state = {
                                "name": value.name,
                                "parent": value.parent,
                                "abstract": value.abstract,
                                "views": {},
                                "ncyBreadcrumb": {
                                    "skip": true
                                }
                            };

                        }

                        if (angular.isDefined(value.controller) && value.controller != null) {
                            state.controller = value.controller;
                        }

                        if (value.abstract === true && value.name == 'main') {
                            var actTemplate = value.views.pop();

                            state.templateUrl = actTemplate.template.url + '?ver=' + dateStr;

                            delete state.views;

                        } else if (value.route === true) {

                            delete state.views;

                        } else {

                            angular.forEach(value.views, function (view) {

                                if (view.template) {

                                    //$templateCache.get()

                                    console.log( view.template );

                                    state.views[view.name] = {
                                        templateUrl: view.template.url + '?ver=' + dateStr,
                                        controller: view.controller
                                    };
                                }

                            });

                        }

                        $stateProviderRef.state(value.name, state);

                        counter++;
                        if (counter == res.data.length) {
                            def.resolve(true);
                        }

                    });
                //});

                return def.promise;
            },
            findOne: function (name) {
                var def = $q.defer();

                _.each($rootScope.routes, function (each) {
                    if (each.name === name) {
                        def.resolve(each);
                    }
                });

                return def.promise;
            }
        };
    })

    .factory('authInterceptor', function ($q,
                                          $location,
                                          AuthDataService,
                                          TokenService,
                                          $cookieStore,
                                          $cookies,
                                          localStorageService,
                                          $rootScope,
                                          $injector,
                                          $config,
                                          $langStorage) {
        return {
            request: function (config) {

                config.headers = config.headers || {};

                config.headers.domainID = $rootScope.domainID;

                var accessTokenName = $config.ACCESS_TOKEN_NAME;

                config.headers.lang = $langStorage.getLangCode();

                if (AuthDataService.getAccessToken()) {
                    config.headers[accessTokenName] = AuthDataService.getAccessToken();
                }

                if (!angular.isDefined($rootScope.user)) {
                    $rootScope.user = {};

                    TokenService.check().then(

                        function (data) {

                            if (data.loggedOut == true) {
                                $rootScope.logged = false;
                                AuthDataService.destroyUserData();
                                TokenService.getNonUserToken().then(function (data) {
                                    AuthDataService.setAccessToken(data.token);
                                    config.headers[accessTokenName] = AuthDataService.getAccessToken();
                                });
                            } else if (_.isObject(data.user)) {
                                $rootScope.logged = true;
                                $rootScope.user = data.user;
                                $rootScope.orderID = data.orderID;
                                $rootScope.oneTimeUser = data.user.onetime;
                                // $rootScope.carts = data.carts;
                                $rootScope.$emit('cartRequired', true)
                            } else {
                                $rootScope.logged = false;
                            }

                        },
                        // fail
                        function (data) {

                         // AuthDataService.checkLogedInOutsideServices();

                            $rootScope.logged = false;

                            if (angular.isDefined(data['noLogin']) && data['noLogin'] == true) {
                                TokenService.getFromCart().then(function (dataCarts) {
                                    // $rootScope.carts = dataCarts.carts;
                                    $rootScope.$emit('cartRequired',true);
                                    $rootScope.orderID = dataCarts.orderID;
                                });
                                AuthDataService.setAccessToken(data.token);
                            } else {
                                TokenService.getNonUserToken().then(function (data) {
                                    AuthDataService.setAccessToken(data.token);
                                    config.headers[accessTokenName] = AuthDataService.getAccessToken();
                                });
                            }

                        });

                }

                config.headers.sourceApp = 'client';

                return config;
            },
            responseError: function (rejection) {
                if (rejection.status === 403) {
                    var Notification = $injector.get('Notification');
                    var $filter = $injector.get('$filter');
                    Notification.info($filter('translate')('you_are_loggedout'));
                    var $state = $injector.get('$state');
                    var $stateParams = $injector.get('$stateParams');
                    var $rootScope = $injector.get('$rootScope');
                    if( $state.current.name !== 'login' ) {
                        $rootScope.startPoint = {
                            'state': $state.current.name,
                            'params': $stateParams
                        };
                    }

                    $state.go('login');
                }
                return $q.reject(rejection);
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
                LoadingService.responsed(response.status);
                $rootScope.$broadcast('loading:finish');
                return response;
            },
            responseError: function (rejection) {

                LoadingService.responsed(rejection.status);

                $rootScope.$broadcast('loading:finish');
                return $q.reject(rejection);
            }
        }
    })
    .factory('catchMailErrorInterceptor', function () {
        return {
            response: function (response) {
                if (response.data.mailInfo && response.data.mailInfo.error) {
                    console.log('Mail Error: ' + response.data.mailInfo.error);
                }
                return response;
            }
        }
    })
    .factory('responseErrorInterceptor', function ($q, $injector, $timeout) {
        return {
            responseError: function (response) {

                if (response.status == 0 || response.status == 408 || response.status > 500) {
                    var $http = $injector.get('$http');
                    return $timeout(function () {
                        return $http(response.config);
                    }, 3000, false);
                } else {
                    return $q.reject(response);
                }

            }
        }
    })
    .factory('readExpiryTimeInterceptor', function ($q) {
    return {
        response: function (response) {
            if (response.headers()['x-http-method-override']) {
                console.log('ok');
            }
        }
    }
})
    .factory('socket', function (socketFactory, $config) {
    var myIoSocket = io.connect($config.SOCKET_URL, {secure: true});

    var mySocket = socketFactory({
        prefix: '',
        ioSocket: myIoSocket
    });

    mySocket.forward('error');
    return mySocket;
})
    .factory('metaTags', function ($q, $http, $config) {
    return {
        getRoute : function (path) {
            var def = $q.defer();
            $http({
                url: $config.API_URL + 'routes/getRouteByUrl',
                method: 'PATCH',
                data:{url : path}
            }).then(function (res) {
                def.resolve(res.data)
            }, function (err) {
                def.reject(new Error(err));
            });
            return def.promise;
        },
        getByGroup: function (groupUrl, categoryUrl) {
            var def = $q.defer();

            $http({
                url: $config.API_URL + 'dp_metaTags' + '?type=' + 'group' + '&' + 'itemUrl=' + groupUrl + '&categoryUrl=' + categoryUrl,
                method: 'GET'
            }).then(function (res) {
                def.resolve(res.data)
            }, function (err) {
                def.reject(new Error(err));
            });

            return def.promise;
        },
        getByType: function (typeUrl, categoryUrl) {
            var def = $q.defer();

            $http({
                url: $config.API_URL + 'dp_metaTags' + '?type=' + 'type' + '&' + 'itemUrl=' + typeUrl + '&categoryUrl=' + categoryUrl,
                method: 'GET'
            }).then(function (res) {
                def.resolve(res.data)
            }, function (err) {
                def.reject(new Error(err));
            });

            return def.promise;
        },
        getByCategory: function (categoryUrl) {

            var def = $q.defer();

            $http({
                url: $config.API_URL + 'dp_metaTags' + '?type=' + 'category' + '&' + 'itemUrl=' + categoryUrl,
                method: 'GET'
            }).then(function (res) {
                def.resolve(res.data)
            }, function (err) {
                def.reject(new Error(err));
            });

            return def.promise;
        }
    };
});

angular.module('dpClient.helpers').directive('myScroll', function () {
    return {
        restrict: "A",
        link: function (scope, element) {
            $(element).on('click', function () {

                $('html, body').animate({
                    scrollTop: 0
                });
                return false;
            });
        }
    };
});

angular.module('dpClient.helpers').directive('initBind', function ($compile) {
    return {
        restrict: 'A',
        link : function (scope, element, attr) {
            attr.$observe('ngBindHtml',function(){
                if(attr.ngBindHtml){
                    $compile(element[0].children)(scope);
                }
            })
        }
    };
});

angular.module('dpClient.helpers').directive('spinnerSlider', function() {
    return {
        restrict: 'E',
        scope: {
            model: '=',      // Wartość liczbową wiążemy dwukierunkowo
            min: '@',        // min, max, step jako stringi z atrybutów
            max: '@',
            step: '@',
            onChange: '&'    // Funkcja wywoływana po zmianie wartości
        },
        bindToController: true,
        controllerAs: 'ctrl',
        template: `
            <div class="input-group spincontainer">
                <div class="input-group-btn">
                    <button type="button" class="btn btn-default" ng-click="ctrl.decrement()" data-dir="dwn">
                        <i class="fa fa-minus"></i>
                    </button>
                </div>
                <input class="form-control spinner-input"
                       type="number"
                       force-number
                       ng-model="ctrl.model"
                       min="{{ctrl.min}}"
                       max="{{ctrl.max}}"
                       step="{{ctrl.step}}"
                       ng-init="ctrl.initModel()"
                       ng-change="ctrl.fixValueAndNotify()" />
                <div class="input-group-btn">
                    <button type="button" class="btn btn-default" ng-click="ctrl.increment()" data-dir="up">
                        <i class="fa fa-plus"></i>
                    </button>
                </div>
            </div>

            <div class="slider-container">
                <input class="form-control slider"
                       type="range"
                       force-number
                       ng-model="ctrl.model"
                       min="{{ctrl.min}}"
                       max="{{ctrl.max}}"
                       step="{{ctrl.step}}"
                       ng-change="ctrl.fixValueAndNotify()" />
                <div class="slider-values">
                    <span class="slider-min">Min: {{ctrl.min}}</span>
                    <span class="slider-max">Max: {{ctrl.max}}</span>
                </div>
            </div>
        `,
        controller: [ '$scope', function($scope) {
            var vm = this;

            // 1) Inicjalizacja wartości jako średniej z min i max
            vm.initModel = function() {
                // jeżeli model już jest przypisany przez rodzica, nie nadpisujemy go
                // ale jeśli nie jest, ustawiamy średnią
                if (typeof vm.model === 'undefined' || vm.model === null) {
                    var minVal = parseFloat(vm.min) || 0;
                    var maxVal = parseFloat(vm.max) || 100;
                    var stepVal = parseFloat(vm.step) || 1;

                    var avg = (minVal + maxVal) / 2;
                    vm.model = roundValueToStep(avg, minVal, maxVal, stepVal);
                } else {
                    // jeżeli już coś jest w modelu, to zafixujemy ją w razie czego
                    vm.fixValueAndNotify();
                }
            };

            // 2) Funkcje do przycisków +/- (decrement/increment)
            vm.decrement = function() {
                var current = parseFloat(vm.model) || 0;
                var stepVal = parseFloat(vm.step) || 1;
                var minVal = parseFloat(vm.min) || 0;
                var maxVal = parseFloat(vm.max) || 100;

                var newVal = current - stepVal;
                // 3) Jeżeli spadniemy poniżej minimum, ustawiamy wartość min
                if (newVal < minVal) {
                    newVal = minVal;
                }
                vm.model = newVal;
                vm.callOnChange();
            };

            vm.increment = function() {
                var current = parseFloat(vm.model) || 0;
                var stepVal = parseFloat(vm.step) || 1;
                var minVal = parseFloat(vm.min) || 0;
                var maxVal = parseFloat(vm.max) || 100;

                var newVal = current + stepVal;
                // 4) Jeżeli przekroczymy maksimum, ustawiamy wartość max
                if (newVal > maxVal) {
                    newVal = maxVal;
                }
                vm.model = newVal;
                vm.callOnChange();
            };

            // 5) Funkcja wywoływana przy zmianie (np. ręcznej w input, suwaku, itp.)
            vm.fixValueAndNotify = function() {
                var minVal = parseFloat(vm.min) || 0;
                var maxVal = parseFloat(vm.max) || 100;
                var stepVal = parseFloat(vm.step) || 1;
                var current = parseFloat(vm.model) || 0;

                // Zaokrąglamy zgodnie z krokiem, jeśli mieści się w min/max
                // + wymuszamy min/max jeśli user wpisał wartości poza zakresem
                vm.model = roundValueToStep(current, minVal, maxVal, stepVal);

                vm.callOnChange();
            };

            // 6) Wywołanie callbacku, jeśli zdefiniowane
            vm.callOnChange = function() {
                if (typeof vm.onChange === 'function') {
                    vm.onChange({ value: vm.model });
                }
            };

            // Funkcja pomocnicza: zaokrągla liczbę do najbliższej wartości (wielokrotności) kroku,
            // dbając o zakres [min, max].
            function roundValueToStep(value, min, max, step) {
                if (value < min) {
                    return min;
                }
                if (value > max) {
                    return max;
                }
                // 2) Zaokrąglamy do wielokrotności kroku
                // Najpierw dzielimy przez step, zaokrąglamy, potem mnożymy z powrotem
                var stepsCount = Math.round(value / step);
                var newVal = stepsCount * step;

                // Upewniamy się, że dalej mieścimy się w zakresie
                if (newVal < min) {
                    newVal = min;
                }
                if (newVal > max) {
                    newVal = max;
                }
                return newVal;
            }

            // 7) Dodatkowo możesz obserwować zmiany w $scope,
            //    jeśli chciałbyś "na żywo" naprawiać wartość.
            //    Tutaj wykorzystujemy "vm.fixValueAndNotify()" w watchu:
            $scope.$watch(function() { return vm.model; }, function() {
                vm.fixValueAndNotify();
            });
        }]
    };
});


angular.module('dpClient.helpers').directive('forceNumber', function() {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function(scope, element, attrs, ngModelCtrl) {
            ngModelCtrl.$parsers.push(function(value) {
                if (typeof value === 'string') {
                    var numVal = parseFloat(value);
                    if (!isNaN(numVal)) {
                        return numVal;
                    }
                }
                return value;
            });

            ngModelCtrl.$formatters.push(function(value) {
                if (typeof value === 'string') {
                    var numVal = parseFloat(value);
                    if (!isNaN(numVal)) {
                        return numVal;
                    }
                }
                return value;
            });
        }
    };
});

$(window).scroll(function () {
    if ($(this).scrollTop() > 200) {
        $('i#scrollTop').fadeIn();
    } else {
        $('i#scrollTop').fadeOut();
    }

});

'use strict';

/**
 * @ngdoc function
 * @name digitalprintFrontendApp.controller:MainCtrl
 * @description
 * # MainCtrl
 * Controller of the digitalprintFrontendApp
 */
angular.module('dpClient.app')
    .controller('cart.CartCtrl', function ($scope, $rootScope, $filter, DpOrderService, DeliveryService, DpProductService,
                                           AddressService, DpAddressService, AuthService, PaymentService,
                                           ProductFileService, UserService, AuthDataService, CalculationService,
                                           CountriesService, RegisterWidget, Notification, FileUploader, $state, $q,
                                           $config, $modal, $timeout, LoginWidgetService, DeliveryWidgetService,
                                           TemplateRootService, CouponService, TokenService, EditorProjectService,
                                           SocialWidgetService, SettingService, CommonService, $sce, CountService,
                                           CartWidgetService, vcRecaptchaService, DpCartsDataService, MainWidgetService) {

        var _timeout;
        var _overallTimeout;

        $scope._ = _;

        $scope.isCollapsed = false;
        $scope.cart = {};
        $scope.deliveries = [];
        $scope.addresses = [];
        $scope.blockCart = false;
        $scope.payments = [];
        $scope.preventPayment = false;
        $scope.paymentsOffset = 0;
        $scope.countries = [];
        $scope.coupons = [];
        $scope.onlyForCompanies = false;
        $scope.confirmButtonInCart = false;
        $scope.userCanRecalculateCart = false;
        $scope.reCountProductExist = false;
        $scope.confirmTextInCart = {};
        $scope.senders = [];
        $scope.confirmButton = false;
        $scope.showSeparateConfirmButton = false;

        $scope.form = {};
        $scope.noRegisterForm = {};

        $scope.canJoinAddresses = false;
        $scope.addressToJoin = {};

        $scope.connectedIndexes = {};
        $scope.connectDeliveryPrices = {};

        $scope.joinedDelivery = {};

        $scope.capthaResponse = null;
        $scope.captchaWidgetId = null;

        $rootScope.$watch('logged', function (logged) {
        });

        $scope.setResponse = function (response) {
            console.info('Captcha response available');
            $scope.capthaResponse = response;
        };
        $scope.setCaptchaWidgetId = function (widgetId) {
            console.info('Created captcha widget ID: %s', widgetId);
            $scope.captchaWidgetId = widgetId;
        };
        $scope.setCaptchaExpiration = function () {
            console.info('Captcha expired. Resetting response object');
            vcRecaptchaService.reload($scope.captchaWidgetId);
            $scope.capthaResponse = null;
        };

        $rootScope.$on('Delivery:change', function (event) {

        });
        $rootScope.$on('delivery', function (e, productAddresses) {
            if ($scope.cart.deliveryConnected) {
                $scope.cart.deliveryGrossPrice = productAddresses[0].priceGross
                $scope.cart.deliveryPrice = productAddresses[0].price
            } else {
                $scope.cart.deliveryGrossPrice = _.reduce($scope.cart.products, (all, product) => {
                    return all + _.reduce(product.addresses, (all, address) => {
                        return all + _.parseFloat(address.priceGross)
                    }, 0)
                }, 0)
                $scope.cart.deliveryPrice = _.reduce($scope.cart.products, (all, product) => {
                    return all + _.reduce(product.addresses, (all, address) => {
                        return all + _.parseFloat(address.price)
                    }, 0)
                }, 0)
            }
            $scope.allDeliveryPrice()
        })
        $rootScope.$on('Cart:copied', function () {
            getCartData();
        });

        $rootScope.$on('Cart:deleted', function () {
            getCartData();
        });

        $rootScope.$on('productFileChanged', function () {
            getCartData();
        });

        var Setting = new SettingService('additionalSettings');

        var init = function () {

            CountriesService.getAll().then(function (dataCountries) {
                $scope.countries = dataCountries;
            });

            Setting.getPublicSettings().then(function(settingsData) {
                if( settingsData.confirmButtonInCart ) {
                    $scope.confirmButtonInCart = settingsData.confirmButtonInCart.value;
                    $scope.confirmTextInCart = settingsData.confirmTextInCart;
                }
                if(settingsData.onlyForCompanies) {
                    $scope.onlyForCompanies = settingsData.onlyForCompanies.value;
                }
                if( settingsData.recalculateInCart ) {
                    $scope.userCanRecalculateCart = settingsData.recalculateInCart.value;
                }
                if( settingsData.separateConfirmButton ) {
                    $scope.showSeparateConfirmButton = settingsData.separateConfirmButton.value;
                }
                if (settingsData.captchaPublicKey) {
                    $scope.model = {
                        key: settingsData.captchaPublicKey.value
                    };
                }
                $scope.fixFile = settingsData.fixFile.value;

            });

            getCartData();

        };

        function getAddresses() {//TODO
            var def = $q.defer();

            if ($rootScope.logged) {

                AddressService.getForUser().then(function (data) {
                    def.resolve(data);
                });

            } else {
                AddressService.getAddressesFromSession().then(function (addresses) {
                    AddressService.getAll(addresses).then(function (data) {
                        def.resolve(data);
                    });
                });
            }

            return def.promise;
        }

        function getCartData() {

            var projects = [];
            $scope.coupons = [];
            $scope.cart.overallAddresses = [{}];
            $scope.connectDeliveryPrices = {};
            $scope.connectedIndexes = {};

            $scope.reCountProductExist = false;
            $scope.dataLoading = true;

            DpOrderService.getCart().then(function (data) {

                if (data.response === false) {
                    $scope.dataLoading = false;
                    return;
                }

                if (data.order !== undefined) {
                    $scope.cart.deliveryConnected = data.order.deliveryConnected;
                    $scope.cart.currency = data.order.currency;
                    $scope.cart.currencySymbol = data.order.currencySymbol;
                    $scope.cart.userMail = data.order.userMail;
                    $scope.cart.userTelephone = data.order.defaultAddress.areaCode + '' + data.order.defaultAddress.telephone;
                    $scope.cart.userFullName = data.order.defaultAddress.name + ' ' + data.order.defaultAddress.lastname;
                }

                DeliveryService.getAll().then(function (deliveries) {

                    PaymentService.getAll(data.order.ID).then(function (paymentsData) {

                        $scope.paymentsOffset = (4 % paymentsData.length) * 3;

                        _.each(paymentsData, function(payment) {
                            if( payment.deferredPayment && payment.creditLimit ) {
                                payment.tooltipInfo = $filter('translate')(payment.infoForUser) + ' ' + payment.creditLimit
                                    + '/' + payment.unpaidValue + ' ' + payment.baseCurrency;
                            } else {
                                payment.tooltipInfo = $filter('translate')('no_credit_limit');
                            }
                        });

                        $scope.payments = paymentsData;

                        $scope.deliveries = deliveries;

                        $scope.cart.deliveryPrice = 0;
                        $scope.cart.deliveryGrossPrice = 0;

                        _.each(data.order.products, function (product, index) {

                            if( product.beforeReCountPriceID > 0 ) {
                                $scope.reCountProductExist = true;
                            }

                            if (typeof product.deliveryPrice === 'string') {
                                product.deliveryPrice = product.deliveryPrice.replace(',', '.');
                            }
                            $scope.cart.deliveryPrice += parseFloat(product.deliveryPrice);
                            if (typeof product.deliveryPriceGross === 'string') {
                                product.deliveryPriceGross = product.deliveryPriceGross.replace(',', '.');
                            }
                            $scope.cart.deliveryGrossPrice += parseFloat(product.deliveryPriceGross);

                            var cartIndex = _.findIndex(data.carts, {productID: product.productID});
                            if (cartIndex > -1 && !_.isEmpty(data.carts[cartIndex].ProductAddresses) && data.carts[cartIndex].ProductAddresses !== null) {
                                if (data.carts[cartIndex].ProductAddresses[0].commonRealisationTime &&
                                    data.carts[cartIndex].ProductAddresses[0].commonDeliveryID > 0) {
                                    var tmpDate = new Date(null);
                                    tmpDate.setTime(data.carts[cartIndex].ProductAddresses[0].commonRealisationTime);
                                    product.realisationDate = tmpDate;
                                } else {
                                    product.realisationDate = Date.parse(product.realisationDate);
                                }
                            }

                            product.addresses = [];
                            var pAddresses;

                            var pIdx = _.findIndex(data.carts, {productID: product.productID});

                            if (pIdx > -1) {
                                pAddresses = data.carts[pIdx].ProductAddresses;
                            }

                            if (!_.isEmpty(pAddresses)) {
                                product.addresses = pAddresses;
                            }


                            product.checked = true;

                            /**
                             *
                             * @param {Array} product.fileList
                             */
                            product.fileList = [];
                            product.lastFile = {};
                            ProductFileService.getAll(product.productID).then(function (attributes) {
                                product.fileList = attributes;
                                product.lastFile = _.last(_.sortBy(attributes, function (sortableFile) {
                                    return sortableFile.created;
                                }));
                                product.availableFilesToFix=false
                                attributes.forEach(attr=>{
                                    if(attr.files.find((file)=>(file.dimensionsValid===0 || file.pagesDiff>0))!=undefined){
                                        product.availableFilesToFix= true
                                    }
                                })

                            });

                            if (product.projectID) {
                                EditorProjectService.getProjectPrev(product.projectID).then(function (prevData) {
                                    if (prevData && prevData.length > 0) {
                                        product.prevPages = prevData;
                                    }
                                });
                            }

                            if(product.projectID) {
                                projects.push(product.projectID);
                            }

                            var findIndex;
                            if( index === (data.order.products.length - 1) && projects.length > 0) {
                                EditorProjectService.getProjectsData(projects).then(function(projectsData) {
                                    if( projectsData.length > 0 ) {
                                        _.each(projectsData, function(oneProject) {
                                            findIndex = -1;
                                            if( oneProject.projectName ) {
                                                findIndex = _.findIndex(data.order.products, {projectID: oneProject._id});
                                                if( findIndex > -1 ) {
                                                    data.order.products[findIndex].projectName = oneProject.projectName;
                                                }
                                            }
                                        });
                                    }
                                });
                            }

                        });
                        $scope.dataLoading = false;
                        $scope.cart.products = data.order.products;
                        $scope.cart.sumPrice = data.order.sumPrice;
                        $scope.cart.sumGrossPrice = data.order.sumGrossPrice;

                        $scope.cart.sumCalcPrice = data.order.sumCalcPrice;
                        $scope.cart.sumCalcGrossPrice = data.order.sumCalcGrossPrice;

                        getAddresses().then(function (allAddress) {

                            $scope.addresses = allAddress.addresses;
                            if($rootScope.logged && $scope.addresses.length==0){
                                fillReceiverAddress(true)
                            }

                        });

                    });

                });
            });

        }

        $scope.$watch('countries', function (countries) {

            if (_.isEmpty(countries)) {
                return;
            }

            RegisterWidget.initCodeRegister($scope, countries);
            RegisterWidget.initCodeWithoutRegister($scope, countries);

        });

        $scope.selectCountry = function (prefix, withoutRegister) {

            if (withoutRegister) {
                RegisterWidget.selectCountryWithoutRegister($scope, prefix);
            } else {
                RegisterWidget.selectCountryRegister($scope, prefix);
            }

        };


        var checkFiles = function () {
            var def = $q.defer();

            var emptyProducts = 0;

            _.each($scope.cart.products, function (product, index) {

                if (product.fileList.length === 0) {
                    emptyProducts++;
                }

                if (index === ($scope.cart.products.length - 1)) {
                    def.resolve(emptyProducts);
                }

            });

            return def.promise;
        };

        $scope.deleteProduct = function (product) {

            CartWidgetService.deleteProduct($scope, product).then(function (response) {
                if (response) {
                    Notification.success($filter('translate')('product_deleted'));
                    getCartData()
                } else {
                    Notification.error($filter('translate')('error'));
                }


            });
        };

        $scope.showDelivery = function (product) {

            showDelivery(product);

        };

        function fillDeliveryInfo(scope, address) {

            var _addressTimeout = null;
            var def = $q.defer();

            var adrIdx = _.findIndex(scope.addresses, {ID: parseInt(address.addressID)});
            if (adrIdx > -1) {
                address.details = scope.addresses[adrIdx];
            }

            var sdrIdx = _.findIndex(scope.senders, {type: parseInt(address.senderID)});
            if (sdrIdx > -1) {
                address.senderName = $filter('translate')(scope.senders[sdrIdx].name);
            }

            var dlvIdx = _.findIndex(scope.filteredDeliveries, {ID: parseInt(address.deliveryID)});
            if (dlvIdx > -1) {
                address.deliveryNames = scope.filteredDeliveries[dlvIdx].names;
            }

            console.log('address: ', address);

            var deliveryIndex = _.findIndex(scope.filteredDeliveries, {ID: address.deliveryID});
            if (deliveryIndex > -1) {
                address.deliveryNames = scope.filteredDeliveries[deliveryIndex].names;
                address.collectionPoints = scope.filteredDeliveries[deliveryIndex].collectionPoints;
                var collectionPointIndex = _.findIndex(
                    scope.filteredDeliveries[deliveryIndex].collectionPoints,
                    {ID: address.collectionPointID});
                if( collectionPointIndex > -1 ) {
                    address.collectionPoint = scope.filteredDeliveries[deliveryIndex].collectionPoints[collectionPointIndex];
                }
            }

            _addressTimeout = $timeout(function(){
                def.resolve(address);
                _addressTimeout = null;
            },500);

            return def.promise;
        }

        function fillDeliveryInfo2(product, address) {

            var _addressTimeout = null;
            var def = $q.defer();

            var adrIdx = _.findIndex(product.addresses, {ID: parseInt(address.addressID)});
            if (adrIdx > -1) {
                address.details = product.addresses[adrIdx];
            }

            var sdrIdx = _.findIndex(product.senders, {type: parseInt(address.senderID)});
            if (sdrIdx > -1) {
                address.senderName = $filter('translate')(product.senders[sdrIdx].name);
            }

            var dlvIdx = _.findIndex(product.filteredDeliveries, {ID: parseInt(address.deliveryID)});
            if (dlvIdx > -1) {
                address.deliveryNames = product.filteredDeliveries[dlvIdx].names;
            }

            _addressTimeout = $timeout(function(){
                def.resolve(address);
                _addressTimeout = null;
            },500);

            return def.promise;
        }

        $scope.allDeliveryPrice = function () {

            var deliveryPrice = 0;
            var deliveryGrossPrice = 0;

            var totalPrice;
            var totalGrossPrice;
            var tmpCalcPrice;
            var tmpCalcGrossPrice;
            var tmpDeliveryGrossPrice;
            var tmpDeliveryPrice;

            if ($scope.cart.sumPrice !== undefined) {
                totalPrice = $scope.cart.sumPrice;
                tmpDeliveryPrice = $scope.cart.deliveryPrice;

                if (typeof(totalPrice) === 'string') {
                    totalPrice = totalPrice.replace(',', '.');
                }
                if (typeof tmpDeliveryPrice === 'string') {
                    tmpDeliveryPrice = tmpDeliveryPrice.replace(',', '.');
                }
                totalPrice = parseFloat(totalPrice) + parseFloat(tmpDeliveryPrice);
            }

            if ($scope.cart.sumCalcPrice !== undefined) {
                tmpCalcPrice = $scope.cart.sumCalcPrice;
                tmpDeliveryPrice = $scope.cart.deliveryPrice;

                if (typeof(tmpCalcPrice) === 'string') {
                    tmpCalcPrice = tmpCalcPrice.replace(',', '.');
                }
                if (typeof tmpDeliveryPrice === 'string') {
                    tmpDeliveryPrice = tmpDeliveryPrice.replace(',', '.');
                }
                tmpCalcPrice = parseFloat(tmpCalcPrice) + parseFloat(tmpDeliveryPrice);
            }

            if ($scope.cart.sumGrossPrice !== undefined) {
                totalGrossPrice = $scope.cart.sumGrossPrice;
                tmpDeliveryGrossPrice = $scope.cart.deliveryGrossPrice;

                if (typeof(totalGrossPrice) === 'string') {
                    totalGrossPrice = totalGrossPrice.replace(',', '.');
                }
                if (typeof tmpDeliveryGrossPrice === 'string') {
                    tmpDeliveryGrossPrice = tmpDeliveryGrossPrice.replace(',', '.');
                }
                totalGrossPrice = parseFloat(totalGrossPrice) + parseFloat(tmpDeliveryGrossPrice);
            }

            if ($scope.cart.sumCalcGrossPrice !== undefined) {
                tmpCalcGrossPrice = $scope.cart.sumCalcGrossPrice;
                tmpDeliveryGrossPrice = $scope.cart.deliveryGrossPrice;

                if (typeof(tmpCalcGrossPrice) === 'string') {
                    tmpCalcGrossPrice = tmpCalcGrossPrice.replace(',', '.');
                }
                if (typeof tmpDeliveryGrossPrice === 'string') {
                    tmpDeliveryGrossPrice = tmpDeliveryGrossPrice.replace(',', '.');
                }
                tmpCalcGrossPrice = parseFloat(tmpCalcGrossPrice) + parseFloat(tmpDeliveryGrossPrice);
            }

            $scope.cart.totalPrice = totalPrice.toFixed(2).replace('.', ',');
            $scope.cart.totalGrossPrice = totalGrossPrice.toFixed(2).replace('.', ',');

            $scope.cart.totalCalcPrice = tmpCalcPrice.toFixed(2).replace('.', ',');
            $scope.cart.totalCalcGrossPrice = tmpCalcGrossPrice.toFixed(2).replace('.', ',');

            $scope.cart.deliveryPrice = parseFloat(tmpDeliveryPrice).toFixed(2).replace('.', ',');
            $scope.cart.deliveryGrossPrice = parseFloat(tmpDeliveryGrossPrice).toFixed(2).replace('.', ',');
        };

        $scope.checkDelivery = function (address) {

            var idx = _.findIndex($scope.deliveries, {ID: address.deliveryID});

            address.turnOffAddress = false;

            if (idx < 0) {
                return;
            }

            var delivery = $scope.deliveries[idx];

            if (angular.isDefined(delivery.module) && Object.keys(delivery.module).length > 0) {

                if (angular.isDefined(delivery.module.keys) && Object.keys(delivery.module.keys).length > 0) {

                    _.each(delivery.module.keys, function (key) {

                        if (key.func === 'collection') {

                            address.turnOffAddress = true;

                        }

                    });

                }

            }

        };

        $scope.saveCartData = function () {

            if (this.blockCart) {
                return;
            }

            var orderID;
            var sendData = {};
            sendData.addresses = {};

            _.each($scope.cart.products, function (product) {

                orderID = product.orderID;
                sendData.addresses[product.ID] = product.addresses;

            });

            sendData.paymentID = $scope.cart.paymentID;
            sendData.orderMessage = $scope.form.orderMessage;

            DpOrderService.saveCart(orderID, sendData).then(function () {

                AuthService.cleanSession().then(function () {

                    $rootScope.carts = [];
                    $rootScope.orderID = null;
                    $state.go('cartVerify');

                });

            });

        };



        $scope.reg = false;
        $scope.no_acct = false;
        $scope._login = true;
        $scope.isActiveReg = false;
        $scope.isActiveNo_acct = false;
        $scope.isActive_login = true;

        $scope.showReg = function () {
            $scope.reg = true;
            $scope.no_acct = false;
            $scope._login = false;
            $scope.isActive = !$scope.isActive;
        };

        $scope.showLogin = function () {
            $scope.reg = false;
            $scope.no_acct = false;
            $scope._login = true;
            $scope.isActive = !$scope.isActive;
        };

        $scope.showCheckout = function () {
            $scope.reg = false;
            $scope.no_acct = true;
            $scope._login = false;
            $scope.isActive = !$scope.isActive;
        };

        init();

        $scope.login = function (credentials) {
            LoginWidgetService.loginInCart($scope, credentials).then(function() {
                getCartData();
            });
        };

        $scope.addUser = function () {
            if ($scope.form.terms === true && $scope.form.data_protection === true) {

                $scope.form.captchaResponse = $scope.capthaResponse;

                UserService.userRegister($scope.form).then(function (data) {
                    if (data.response) {
                        var credentials = {};
                        credentials.password = $scope.form.pass;
                        credentials.email = $scope.form.user;

                        $scope.cart.userMail = data.user.user;
                        if( data.address ) {
                            $scope.cart.userTelephone = data.address.areaCode + '' + data.address.telephone;
                            $scope.cart.userFullName = data.address.name + ' ' + data.address.lastname;
                        }

                        LoginWidgetService.loginInCart($scope, credentials).then(function() {
                            getCartData();
                        });

                    } else {
                        if (data.info.length > 0) {
                            Notification.error($filter('translate')(data.info));
                        } else {
                            Notification.error($filter('translate')('error'));
                        }
                    }

                }, function (data) {
                    Notification.error($filter('translate')('unexpected_error'));
                });
            } else {
                Notification.error($filter('translate')('accept_terms'));
            }
        };

        $scope.addNonRegister = function () {

            if ($scope.noRegisterForm.terms !== true || $scope.noRegisterForm.data_protection !== true) {
                Notification.error($filter('translate')('accept_terms'));
                return;
            }

            checkFiles().then(function (emptyProducts) {

                if (emptyProducts > 0) {
                    Notification.error($filter('translate')('to_order_add_file'));
                    return;
                }

                $scope.noRegisterForm.oneTimeUser = 1;
                $scope.noRegisterForm.captchaResponse = $scope.capthaResponse;

                UserService.userRegister($scope.noRegisterForm).then(function (data) {

                    console.log(data);

                    var credentials = {};
                    credentials.password = data.user.ID;
                    credentials.email = data.user.user + '_' + data.user.ID;

                    $scope.cart.userMail = data.user.user;
                    if( data.address ) {
                        $scope.cart.userTelephone = data.address.areaCode + '' + data.address.telephone;
                        $scope.cart.userFullName = data.address.name + ' ' + data.address.lastname;
                    }

                    LoginWidgetService.loginInCart($scope, credentials, true).then( function() {
                        getCartData();
                    });

                }, function err(data) {
                    if (data.info.length > 0) {
                        Notification.error($filter('translate')(data.info));
                    } else {
                        Notification.error($filter('translate')('unexpected_error'));
                    }
                });

            });

        };

        $scope.continueShopping = function () {
            $state.go('home');
        };

        $scope.paymentConfirm = function (paymentID) {

            var paymentIdx = _.findIndex($scope.payments, {ID: paymentID});

            if( paymentIdx > -1 ) {
                var payment = $scope.payments[paymentIdx];

                if( payment.deferredPayment && !payment.creditLimit ) {
                    Notification.error($filter('translate')('no_credit_limit'));
                    return;
                }

                if( payment.limitExceeded ) {
                    Notification.error($filter('translate')('credit_limit_exceeded') + ' - ' +
                        payment.creditLimit + '/' +  payment.unpaidValue + ' ' + payment.baseCurrency );
                    return;
                }

                resetPayments().then(function() {
                    payment.selected = true;
                });
            }

            if( $scope.confirmButtonInCart ) {
                if( !$scope.form.confirmStatute ) {
                    Notification.error($filter('translate')('confirm_statute_is_required'));
                    return;
                }
            }

            checkSelfCollectDelivery($scope.cart.products).then(function(collectDeliveries) {

                if ($scope.addresses.length === 0 && !collectDeliveries) {

                    fillReceiverAddress();

                } else {

                    var incorrectProduct = 0;
                    _.each($scope.cart.products, function (product) {
                        if( _.isEmpty(product.addresses)) {
                            //showDelivery(product);
                            incorrectProduct++;
                        }
                    });

                    if( incorrectProduct > 0 ) {
                        Notification.error($filter('translate')('choose_delivery'));
                        return;
                    }

                    Setting.getPublicSettings().then(function(settingsData) {
                        if( settingsData.onlyForCompanies && settingsData.onlyForCompanies.value === 1 ) {
                            DpAddressService.getDefaultAddress(2).then(function (invoiceData) {
                                if( invoiceData.address.length === 0 ) {
                                    fillInvoiceAddress();
                                } else {
                                    if( settingsData.separateConfirmButton && settingsData.separateConfirmButton.value === 1 ) {
                                        showConfirmButton(payment);
                                    } else {
                                        $scope.preventPayment = true;
                                        doConfirmation(paymentID);
                                    }
                                }
                            });
                        } else {
                            if( settingsData.separateConfirmButton && settingsData.separateConfirmButton.value === 1 ) {
                                showConfirmButton(payment);
                            } else {
                                $scope.preventPayment = true;
                                doConfirmation(paymentID);
                            }
                        }

                    });

                }



            });

        };

        $scope.confirmStatuteCheck = function() {
            if( this.form.confirmStatute ) {
                var payment = _.find($scope.payments, { selected: true });
                if(payment) {
                    $scope.confirmButton = true;
                }
            } else {
                $scope.confirmButton = false;
            }
        };

        $scope.confirmOrder = function() {
            var payment = _.find($scope.payments, { selected: true });

            if( payment ) {
                doConfirmation(payment.ID);
            } else {
                Notification.info($filter('translate')('select_a _payment_method'));
            }
        };

        function showConfirmButton(payment) {

            $scope.confirmButton = true;

        }

        function resetPayments() {

            var def = $q.defer();

            $scope.payments.forEach(function(element, index) {
                element.selected = false;
                if( ($scope.payments.length -1 ) === index ) {
                    def.resolve(true);
                }
            });

            return def.promise;
        }

        function doConfirmation(paymentID) {

            var orderID;
            var sendData = {};
            sendData.addresses = {};

            _.each($scope.cart.products, function (product) {

                orderID = product.orderID;
                sendData.addresses[product.ID] = product.addresses;

            });

            sendData.paymentID = paymentID;
            sendData.orderMessage = $scope.form.orderMessage;

            DpOrderService.saveCart(orderID, sendData).then(function (_cartData) {
                if (_cartData.payment.status) {
                    $rootScope.$emit('cartRequired')
                    if (_cartData.payment.status.statusCode === "SUCCESS" && _cartData.payment.operator == 'payu') {

                        AuthService.cleanSession().then(function () {
                            $rootScope.carts = [];
                            $rootScope.orderID = null;
                            window.location.href = _cartData.payment.redirectUri;
                        });
                    } else if(_cartData.payment.status === 'NEW' && _cartData.payment.operator == 'tinkoff') {

                        AuthService.cleanSession().then(function () {
                            $rootScope.carts = [];
                            $rootScope.orderID = null;
                            window.location.href = _cartData.payment.url;
                        });
                    } else if(_cartData.payment.status === 'NEW' && _cartData.payment.operator == 'sberbank') {

                        AuthService.cleanSession().then(function () {
                            $rootScope.carts = [];
                            $rootScope.orderID = null;
                            window.location.href = _cartData.payment.url;
                        });
                    } else if(_cartData.payment.status === 'CREATED' && _cartData.payment.operator == 'paypal') {

                        AuthService.cleanSession().then(function () {
                            $rootScope.carts = [];
                            $rootScope.orderID = null;
                            window.location.href = _cartData.payment.url;
                        });
                    } else {
                        Notification.error($filter('translate')('payment_rejected'));
                    }
                } else {
                    AuthService.cleanSession().then(function (data) {
                        $rootScope.carts = [];
                        $rootScope.orderID = null;
                        $state.go('cartVerify', {orderid: orderID});
                        $rootScope.$emit('cartRequired')
                    });

                }
            });
        }

        $scope.editName = function (product) {

            if (_timeout) {
                $timeout.cancel(_timeout);
            }

            _timeout = $timeout(function () {
                var CalculateService = new CalculationService(product.groupID, product.typeID);
                CalculateService.updateName({
                    name: product.name,
                    productID: product.productID
                }).then(function (response) {
                    if (response.response == true) {
                        Notification.success($filter('translate')('saved_message'));
                    }
                });
            }, 1000);

        };

        $scope.showOldPrice = function (oldPrice, newPrice) {
            if (typeof oldPrice === 'string') {
                oldPrice = oldPrice.replace(',', '.');
            }
            if (typeof newPrice === 'string') {
                newPrice = newPrice.replace(',', '.');
            }
            return parseFloat(oldPrice) > parseFloat(newPrice);
        };

        $scope.sendCoupon = function () {
            var coupon = this.form.couponID;
            this.form.couponID = null;
            CouponService.check(coupon, $rootScope.orderID).then(function (data) {
                if (data.response) {
                    DpOrderService.updatePrice().then(function (updateData) {

                        if( updateData.response === true ) {
                            if( updateData.messages.length > 0 ) {
                                _.each(updateData.messages, function(msg) {
                                    Notification.success($filter('translate')(msg));
                                });
                            }
                            getCartData();
                        } else {
                            if( updateData.messages.length > 0 ) {
                                _.each(updateData.messages, function(msg) {
                                    Notification.error($filter('translate')(msg));
                                });
                            }
                        }

                    });
                } else {
                    if( data.info ) {
                        _.each(data.info.results, function(oneResult) {
                            if( oneResult.valid ) {
                                Notification.success( $filter('translate')(oneResult.reason) );
                            } else {
                                Notification.error( $filter('translate')(oneResult.reason) );
                            }
                        });
                        Notification.error( $filter('translate')(data.info) );
                    } else {
                        Notification.error($filter('translate')('error'));
                    }
                }
            }, function (data) {
                Notification.error($filter('translate')(data.info));
            });
        };

        function fillReceiverAddress(requiredSave) {
            console.log('Musisz posiadać address');

            TemplateRootService.getTemplateUrl(97).then(function (response) {
                $modal.open({
                    templateUrl: response.url,
                    scope: $scope,
                    size: 'lg',
                    keyboard:!requiredSave,
                    backdrop:requiredSave?'static':true,
                    controller: function ($scope, $modalInstance) {
                        $scope.requiredSave = requiredSave;
                        $scope.saveAddress = function () {

                            this.form.default = 1;

                            DpAddressService.addAddress($scope.form, 1).then( function(data) {
                                if(data.response === true) {
                                    $scope.addresses.push(data.item);
                                    var params = {addressID: data.item.ID};
                                    AuthService.updateDefaultAddress(params).then(function () {
                                        addAddressToOrder(data.item.ID);
                                        Notification.success($filter('translate')('added'));
                                        $rootScope.$emit('addressesChanged')
                                        $modalInstance.close();
                                    });
                                } else {
                                    Notification.error($filter('translate')('error'));
                                }
                            }, function(data) {
                                Notification.error($filter('translate')('error'));
                            });

                        };

                        $scope.cancel = function () {
                            $modalInstance.close();
                        }

                        $scope.isCountryCode = function () {
                            var country = _.find($scope.countries, {code: $scope.form.countryCode});
                            return country && String(country.areaCode).length > 0;
                        }

                        $scope.updateAreaCode = function () {
                            var country = _.find($scope.countries, {code: $scope.form.countryCode});
                            $scope.form.areaCode = country.areaCode;
                        }
                    }
                });

            });

        }

        function fillInvoiceAddress() {

            console.log('Musisz podać dane do faktury!');

            TemplateRootService.getTemplateUrl(98).then(function (response) {
                $modal.open({
                    templateUrl: response.url,
                    scope: $scope,
                    size: 'lg',
                    controller: function ($scope, $modalInstance) {

                        $scope.saveAddress = function () {

                            this.form.default = 1;

                            DpAddressService.addAddress($scope.form, 2).then( function(data) {
                                if(data.response === true) {
                                    Notification.success($filter('translate')('added'));
                                    $modalInstance.close();
                                } else {
                                    Notification.error($filter('translate')('error'));
                                }
                            }, function(data) {
                                Notification.error($filter('translate')('error'));
                            });

                        };

                        $scope.cancel = function () {
                            $modalInstance.close();
                        }

                        $scope.isCountryCode = function () {
                            var country = _.find($scope.countries, {code: $scope.form.countryCode});
                            return country && String(country.areaCode).length > 0;
                        }

                        $scope.updateAreaCode = function () {
                            var country = _.find($scope.countries, {code: $scope.form.countryCode});
                            $scope.form.areaCode = country.areaCode;
                        }
                    }
                });

            });

        }

        $scope.changeVolumes = function(product) {

            var _this = this;
            if(_timeout){
                $timeout.cancel(_timeout);
            }

            var allVolumes = 0;

            _.each(product.productAddresses, function(oneAddress, index) {
                allVolumes += parseInt(oneAddress.allVolume);
                DeliveryWidgetService.getPkgWeight(product, oneAddress, product.filteredDeliveries);
                checkDeliveryParcelShops(oneAddress);
                checkDeliveryCollectionPoints(oneAddress);
            });

            _timeout = $timeout(function(){

                var selectedVolume = product.volume;
                if( product.amount > 1 ) {
                    selectedVolume *= product.amount;
                }

                if( allVolumes > selectedVolume ){
                    var over = allVolumes - selectedVolume;

                    product.productAddresses[_this.$index].allVolume -= Number(over);
                    product.deliveryLackOfVolume = 0;

                    Notification.error($filter('translate')('volume_exceeded_by') + ' ' + over);

                } else if( allVolumes <= selectedVolume ) {

                    product.deliveryLackOfVolume = Number(selectedVolume - allVolumes);

                }

                _timeout = null;
            },500);
        };


        function checkDeliveryParcelShops(productAddress) {

            var deliveryIndex = _.findIndex(productAddress.deliveries, {ID: productAddress.deliveryID});
            if( deliveryIndex > -1 ) {

                if( productAddress.deliveries[deliveryIndex].hasParcelShops && !productAddress.parcelShops ) {

                    productAddress.hasParcelShops = true;
                    productAddress.parcelShops = null;

                    DeliveryWidgetService.findParcelShops(
                        productAddress.addressID,
                        productAddress.deliveries[deliveryIndex].ID,
                        productAddress.deliveries[deliveryIndex].courierID,
                        productAddress
                    ).then( function(result) {
                        console.log(result);
                    });
                } else if ( productAddress.deliveries[deliveryIndex].hasParcelShops && productAddress.parcelShops ) {
                    productAddress.hasParcelShops = true;
                } else {
                    productAddress.hasParcelShops = false;
                }
            }
        }

        function checkDeliveryCollectionPoints(productAddress) {

            var deliveryIndex = _.findIndex(productAddress.deliveries, {ID: productAddress.deliveryID});
            if( deliveryIndex > -1 ) {

                if(productAddress.deliveries[deliveryIndex].module.func === 'collectionAttributes') {

                    productAddress.collectionPointID = productAddress.deliveries[deliveryIndex].collectionPoints[0].ID;
                    productAddress.collectionPoint = productAddress.deliveries[deliveryIndex].collectionPoints[0];
                    productAddress.collectionPoints = productAddress.deliveries[deliveryIndex].collectionPoints;

                } else {
                    delete productAddress.collectionPointID;
                    delete productAddress.collectionPoint;
                    delete productAddress.collectionPoints;
                }
            }


        }

        $scope.displayFlipBook = function (product) {

            if( product.prevPages === undefined ) {
                return;
            }

            var flipbookHolder = document.createElement('div');
            flipbookHolder.className = 'flipbook-holder';

            var remove = document.createElement('div');
            remove.className = 'remove-flipbook';
            remove.innerHTML = 'x';

            var nextPage = document.createElement('div');
            nextPage.className = 'nextPage-flipbook';
            nextPage.innerHTML = '<i class="fa fa-arrow-right" aria-hidden="true"></i>';

            var prevPage = document.createElement('div');
            prevPage.className = 'prevPage-flipbook';
            prevPage.innerHTML = '<i class="fa fa-arrow-left" aria-hidden="true"></i>';

            flipbookHolder.appendChild(remove);
            flipbookHolder.appendChild(nextPage);
            flipbookHolder.appendChild(prevPage);

            document.body.appendChild(flipbookHolder);


            var html = '<div id="flipbook">' +
                '<div class="hard"> Turn.js </div>' +
                '<div class="hard"></div>';

            for (var i = 0; i < product.prevPages.length; i++) {

                html += '<div class=""><img loading="lazy" ng-src="' + product.prevPages[i] + '"></div>';

            }

            html += '<div class="hard"></div>' +
                '<div class="hard"></div>' +
                '</div>';

            flipbookHolder.innerHTML += html;

            var image = new Image();
            image.onload = function () {

                var width = window.innerWidth * 0.8;
                var aspect = width / (this.width * 2);
                var height = this.height * aspect;

                if (height > window.innerHeight) {

                    height = window.innerHeight * 0.8;
                    aspect = height / this.height;
                    width = (this.width * 2) * aspect;
                }

                flipbookHolder.style.paddingTop = (height - window.innerHeight) / 2 + "px";

                $("#flipbook").turn({
                    height: height,
                    width: width,
                    autoCenter: true
                });

                $('.remove-flipbook').on('click', function (e) {
                    e.stopPropagation();
                    $(this).parent().remove();
                });

                $('.nextPage-flipbook').on('click', function (e) {
                    $("#flipbook").turn('next')
                });

                $('.prevPage-flipbook').on('click', function (e) {
                    $("#flipbook").turn("previous");
                });

                $(document).keyup(function(e) {
                    if (e.keyCode === 27) {
                        $("#flipbook").turn("destroy").remove();
                    }
                    e.stopPropagation();
                });

            };

            image.src = product.prevPages[0];

        };

        function addAddressToOrder(addressID) {
            _.each($rootScope.carts, function(order) {
                if( !order.ProductAddresses ) {
                    _.each($scope.cart.products, function (product) {
                        if( _.isEmpty(product.addresses)) {
                            //showDelivery(product);
                        }
                    });
                } else {
                    order.ProductAddresses[0].addressID = addressID;
                }
            });
        }

        function checkSelfCollectDelivery(products) {
            var def = $q.defer();

            var countAddresses = 0;
            var countCollectionPoints = 0;
            var iterator = 0;
            var productIterator = 0;

            _.each(products, function(oneProduct) {
                countAddresses += oneProduct.addresses.length;
                productIterator++;
                _.each(oneProduct.addresses, function(oneAddress) {
                    if( oneAddress.collectionPointID !== undefined || oneAddress.collectionPointID > 0 ) {
                        countCollectionPoints++;
                    }
                    iterator++;

                    if( iterator === countAddresses && productIterator === products.length) {
                        if(countCollectionPoints === countAddresses) {
                            def.resolve(true);
                        } else {
                            def.resolve(false);
                        }
                    }// TODO Co jeśli nie ustawione
                })
            });

            return def.promise;
        }

        $scope.loginFacebook = function () {

            SocialWidgetService.loginFacebook();

        };

        $scope.loginGoogle = function () {

            SocialWidgetService.loginGoogle();

        };

        $scope.insertHtml = function(string) {
            return $sce.trustAsHtml(string);
        };

        $scope.reCalculateCart = function() {

            var data = $scope.cart;

            CountService.reCalculateCart(data).then( function(responseData) {
                 if( responseData.response ) {
                     getCartData();
                     Notification.success($filter('translate')('saved_message'));
                 } else {
                     Notification.warning($filter('translate')('no_price_has_been_changed'));
                 }
            });

        };

        $scope.editProduct = function(product) {
            CartWidgetService.copyProduct($scope, product, false,false, true);
        };

        $scope.copyProduct = function(product) {
            CartWidgetService.copyProduct($scope, product);
        };

        $scope.changeOnlyVolume = function(product) {
            CartWidgetService.copyProduct($scope, product, true);
        };

        /**
         *
         * @param schemType 0 - single 1 - multiple
         */
        $scope.changeDeliveryConnected = function (item) {
            DpOrderService.edit($scope.cart.products[0].orderID, {deliveryConnected : item.value}).then(data=>{
                if(!data.response){
                    Notification.error($filter('translate')('error'));return;
                }
                $scope.cart.deliveryConnected = item.value;
                if($scope.cart.deliveryConnected){
                    $scope.cart.products[0].addresses=[_.clone($scope.cart.products[0].addresses[0])]
                    $scope.cart.products.forEach((product)=>{
                        product.addresses=_.clone($scope.cart.products[0].addresses);
                        product.addresses[0].volume=product.addresses[0].allVolume=product.volume;
                    })
                }else{
                    $scope.cart.products.forEach((product,i)=>{
                        product.addresses.forEach((address,j)=>{
                            $scope.cart.products[i].addresses[j]=_.clone($scope.cart.products[i].addresses[j],true)
                            $scope.cart.products[i].addresses[j].allVolume=product.volume
                        })
                    })

                }
            },err=>{
                Notification.error($filter('translate')('error'))
            })

        }

        const topSpace = 100

        $scope.sectionLinkClick = e => {
            e.preventDefault()

            const name = e.currentTarget.getAttribute('href').substr(1)
            const section = document.querySelector(`section[id=${name}]`)

            $('html').animate({
                scrollTop: section.offsetTop - topSpace
            });
        }
        const scrollFunction = e => {
            const scrollY = window.pageYOffset;
            const sections = document.querySelectorAll('section')
            sections.forEach(section => {
                const toTop = section.getBoundingClientRect().top + window.pageYOffset;
                const relLink = document.querySelector(`a[href*=${section.getAttribute('id')}]`)
                if (window.pageYOffset > toTop - topSpace && window.pageYOffset < toTop + section.getBoundingClientRect().height - topSpace) {
                    relLink.classList.add('active');
                } else {
                    relLink.classList.remove('active');
                }
            })
        }

        window.addEventListener('scroll', scrollFunction);

        $scope.$on('$stateChangeStart', (event, toState, toParams, fromState, fromParams) => {
            window.removeEventListener('scroll',scrollFunction);
        })
        $scope.deliveryConnectedLabel = (item) => $filter('translate')(item.name)
        $scope.compareDeliveryMode = (item) => item.value == $scope.cart.deliveryConnected;


    });

'use strict';

angular.module('dpClient.app')
    .controller('index.AttributeFilters', function ($scope, $rootScope, $filter, $location, AttributeFiltersService, SettingService) {
        var filterParts = [];
        var allOptions;
        var allProductsUsingOptions;
        var attrID = null;
        var Setting = new SettingService('additionalSettings');
        Setting.getPublicSettings().then(function (settingsData) {
            attrID = settingsData.filteredAttribute.value;
            loadAttributeFilters();
        });
        var papersPerPage = 20;

        var filterConfig = {};

        $scope.alternativePapers = [];

        $scope.numberOfPagesInPagination = 6;
        $scope.currentDisplayedCategories = [];
        $scope.currentDisplayedMaterialName = '';
        $scope.currentDisplayPapersType = 'default';
        $scope.choosenTypeID = null;
        $scope.currentDisplayPapersPage = 1;
        $scope.currentDisplayPapersPages = 1;
        $scope.currentDisplayPapersPageData = [];
        $scope.filtersUsed = false;
        $scope.visibleSection = {};

        function loadAttributeFilters() {
            AttributeFiltersService.getOptions(attrID).then(function (data) {
                _.each(data, function (item) {
                    item.descriptions.weight = item.weight
                    _.each(['certificates', 'printingTechniques', 'color_hex', 'application'],
                        function (name) {
                            item.descriptions[name] = '';
                            if(item.descriptions[name].includes(',')){
                                item.descriptions[name] = _.map(item.descriptions[name].split(','),
                                function (value) {
                                    return value.trim()
                                })
                            }
                        })
                })
                allOptions = data;
            }, function (error) {

            }).then(function () {
                AttributeFiltersService.getProductsUsingOptions(attrID).then(function (data) {
                    allProductsUsingOptions = data;
                }, function (error) {

                });

                AttributeFiltersService.getAttributeFilters(attrID)
                    .then(function (data) {
                        filterConfig = data.filterConfig;
                        filterParts = createFilterPart(filterParts, 'name', 'text', data.filterConfig, 'name_of_atrritute_' + attrID);
                        filterParts = createFilterPart(filterParts, 'weight', 'range', data.filterConfig, null, false, 0);
                        filterParts = createFilterPart(filterParts, 'whiteness', 'range', data.filterConfig, null, false, 0);
                        filterParts = createFilterPart(filterParts, 'thickness', 'range', data.filterConfig, null, false, 3);
                        filterParts = createFilterPart(filterParts, 'opacity', 'range', data.filterConfig, null, false, 0);
                        filterParts = createFilterPart(filterParts, 'roughness', 'range', data.filterConfig, null, false, 0);
                        filterParts = createFilterPart(filterParts, 'certificates', 'multi-select', data.filterConfig);
                        filterParts = createFilterPart(filterParts, 'printingTechniques', 'multi-select', data.filterConfig);
                        filterParts = createFilterPart(filterParts, 'application', 'multi-select', data.filterConfig);
                        filterParts = createFilterPart(filterParts, 'color_hex', 'multi-select-color', data.filterConfig, 'paper_color');
                        filterParts = createFilterPart(filterParts, 'ids', '', {}, '', true);
                        $scope.filterParts = _.cloneDeep(filterParts);
                        $scope.categoriesTree = data.filterConfig.categoriesTree;

                        $scope.showAllPapers();

                        var searchObject = $location.search();

                        if (searchObject.showGroup) {
                            var choosenTypeID = null;
                            if (searchObject.markPaper) {
                                choosenTypeID = searchObject.markPaper;
                            }
                            $scope.showGroup(searchObject.showGroup, choosenTypeID);
                        }

                    }, function (error) {
                    });
            });
        }

        function createFilterPart(items, name, type, filterConfig, label, hidden, precision) {
            items = _.clone(items);
            var item = { name: name, type: type, title: !!label ? label : name, hidden: hidden };
            switch (type) {
                case 'multi-select':
                case 'multi-select-color':
                    item.values = filterConfig[name].values;
                    item.selectedValues = {};
                    break;
                case 'range':
                    item.minValue = filterConfig[name].minValue;
                    item.maxValue = filterConfig[name].maxValue;
                    var diff = filterConfig[name].maxValue - filterConfig[name].minValue
                    var step = 1
                    if (diff < 1) {
                        step = 0.01;
                    } else if (diff < 10) {
                        step = 0.1;
                    } else if (diff < 100) {
                        step = 1
                    } else {
                        step = Math.round(diff / 50);
                    }
                    item.options = {
                        floor: filterConfig[name].minValue,
                        ceil: filterConfig[name].maxValue,
                        step: step,
                        precision: precision,
                        onChange: function () {
                            $scope.onInputChange.apply(this)
                        }
                    }
                    break;
            }
            items.push(item);
            return items;
        };

        $scope.onPaperDefaultClick = function (row) {
            console.log(row);
            var category = row.descriptions.category[0].trim();
            var group = row.descriptions.group[0].trim();
            var type = row.descriptions.paper_type[0].trim();
            if(type.endsWith(' ')){
                type = type.slice(0, -1);
            }
            var data = $scope.categoriesTree[category][group][type];
            $scope.choosenTypeID = row.ID;
           $scope.onTypeClick(category, group, type, data);
           $scope.currentDisplayedMaterialName = type;
           $scope.currentDisplayedCategories = [];
           setTimeout(function(){
                  $scope.currentDisplayPapersType = 'papers';
           }, 1500);
        };

        $scope.loadAllPapers = function () {
            var agregateIDS = [];
            for (var category in $scope.categoriesTree) {
                for (var group in $scope.categoriesTree[category]) {
                    for (var type in $scope.categoriesTree[category][group]) {
                        _.each($scope.categoriesTree[category][group][type].IDS,function(singleID){
                            agregateIDS.push(singleID);
                        });
                    }
                }
            }
            agregateIDSFilter = [];
            $scope.onInputChange();
        };

        $scope.showAllPapers = function () {
            $scope.currentDisplayPapersType = 'default';
            $scope.currentDisplayedCategories = [];
            for (var categoryName in $scope.categoriesTree) {
                var tmpObject = {};
                tmpObject.name = categoryName;
                tmpObject.category = categoryName;
                tmpObject.group = '';
                tmpObject.type = '';
                tmpObject.typeData = {};
                tmpObject.displayType = 'category';
                $scope.currentDisplayedCategories.push(tmpObject);
            }
            $scope.currentDisplayedMaterialName = $filter('translate')('materials');
            $scope.loadAllPapers();
        };

        $scope.showCategory = function (showCategoryName) {
            $scope.currentDisplayPapersType = 'default';
            $scope.currentDisplayedCategories = [];
            var showCategoryObject = {};
            for (var categoryName in $scope.categoriesTree) {
                $scope.currentDisplayedCategories.push(tmpObject);
            }
            $scope.currentDisplayedMaterialName = $filter('translate')('materials');
            $scope.loadAllPapers();
            $scope.onCurrentCategoryClick(showCategoryObject);
        };

        $scope.showGroup = function (showGroupName, choosenTypeID ) {
            $scope.currentDisplayPapersType = 'default';
            $scope.currentDisplayedCategories = [];
            var showGroupObject = {};
            for (var categoryName in $scope.categoriesTree) {
                var tmpObject = {};
                tmpObject.name = categoryName;
                tmpObject.category = categoryName;
                tmpObject.group = '';
                tmpObject.type = '';
                tmpObject.typeData = {};
                tmpObject.displayType = 'category';
                $scope.currentDisplayedCategories.push(tmpObject);
                if(categoryName.replace(/\s+/g, '') == showGroupName.replace(/\s+/g, '')){
                    showGroupObject = tmpObject;
                }
                for (var groupName in $scope.categoriesTree[categoryName]) {
                    var tmpObject2 = {};
                    tmpObject2.name = groupName;
                    tmpObject2.category = categoryName;
                    tmpObject2.group = groupName;
                    tmpObject2.type = '';
                    tmpObject2.typeData = {};
                    tmpObject2.displayType = 'group';
                    if(groupName.replace(/\s+/g, '') == showGroupName.replace(/\s+/g, '')){
                        showGroupObject = tmpObject2;
                    }
                    for (var typeName in $scope.categoriesTree[categoryName][groupName]) {
                        var tmpObject3 = {};
                        tmpObject3.name = typeName;
                        tmpObject3.category = categoryName;
                        tmpObject3.group = groupName;
                        tmpObject3.type = typeName;
                        tmpObject3.typeData = $scope.categoriesTree[categoryName][groupName][typeName];
                        tmpObject3.displayType = 'type';
                        if(typeName.replace(/\s+/g, '') == showGroupName.replace(/\s+/g, '')){
                            showGroupObject = tmpObject3;
                        }
                    }
                }
            }
            $scope.currentDisplayedMaterialName = $filter('translate')('materials');
            $scope.loadAllPapers();
            $scope.onCurrentCategoryClick(showGroupObject);
            if(choosenTypeID){
                $scope.choosenTypeID = choosenTypeID;
            }
        };

        var agregateIDSFilter = [];
        $scope.onCurrentCategoryClick = function (clickedCategory) {
            if (clickedCategory.displayType === 'category') {
                $scope.currentDisplayedCategories = [];
                for (var categoryName in $scope.categoriesTree[clickedCategory.category]) {
                    var tmpObject = {};
                    tmpObject.name = categoryName;
                    tmpObject.category = clickedCategory.category;
                    tmpObject.group = categoryName;
                    tmpObject.type = '';
                    tmpObject.typeData = {};
                    tmpObject.displayType = 'group';
                    $scope.currentDisplayedCategories.push(tmpObject);

                    var agregateIDS = [];
                    for (var group in $scope.categoriesTree[clickedCategory.category]) {
                        for (var type in $scope.categoriesTree[clickedCategory.category][group]) {
                            _.each($scope.categoriesTree[clickedCategory.category][group][type].IDS, function(singleID){
                                agregateIDS.push(singleID);
                            });
                        }
                    }
                    agregateIDSFilter = agregateIDS;
                    $scope.onInputChange();
                }
                $scope.currentDisplayedMaterialName = clickedCategory.category;
                $scope.currentDisplayPapersType = 'default';
            }
            if (clickedCategory.displayType === 'group') {
                $scope.currentDisplayedCategories = [];
                for (var categoryName in $scope.categoriesTree[clickedCategory.category][clickedCategory.group]) {
                    var tmpObject = {};
                    tmpObject.name = categoryName;
                    tmpObject.category = clickedCategory.category;
                    tmpObject.group = clickedCategory.group;
                    tmpObject.type = categoryName;
                    tmpObject.typeData = $scope.categoriesTree[clickedCategory.category][clickedCategory.group][categoryName];
                    tmpObject.displayType = 'type';
                    $scope.currentDisplayedCategories.push(tmpObject);

                    var agregateIDS = [];
                    for (var type in $scope.categoriesTree[clickedCategory.category][clickedCategory.group]) {
                        _.each($scope.categoriesTree[clickedCategory.category][clickedCategory.group][type].IDS,function(singleID){
                            agregateIDS.push(singleID);
                        });
                    }
                    agregateIDSFilter = agregateIDS;
                    $scope.onInputChange();
                }
                $scope.currentDisplayedMaterialName = clickedCategory.group;
                $scope.currentDisplayPapersType = 'default';
            }
            if (clickedCategory.displayType === 'type') {
                $scope.choosenTypeID = null;
                $scope.onTypeClick(clickedCategory.category, clickedCategory.group, clickedCategory.type, clickedCategory.typeData);
                $scope.currentDisplayedCategories = [];
                var tmpObject = {};
                tmpObject.name = clickedCategory.name;
                tmpObject.category = clickedCategory.category;
                tmpObject.group = clickedCategory.group;
                tmpObject.type = clickedCategory.type;
                tmpObject.typeData = clickedCategory.typeData;
                tmpObject.displayType = 'typeCurrent';
                $scope.currentDisplayedCategories.push(tmpObject);
                $scope.currentDisplayedMaterialName = clickedCategory.type;

                var agregateIDS = [];
                _.each($scope.categoriesTree[clickedCategory.category][clickedCategory.group][clickedCategory.type].IDS,function(singleID){
                    agregateIDS.push(singleID);
                });
                agregateIDSFilter = agregateIDS;
                $scope.onInputChange();
                $scope.currentDisplayPapersType = 'papers';
            }
        };

        var timerId;

        $scope.onInputChange = function (force) {
            clearTimeout(timerId);
            if (!(force === true)) {
                timerId = setTimeout(function () {
                    $scope.onInputChange(true);
                }, 1000);
                return
            }
            $scope.filtersUsed = true;
            AttributeFiltersService.search(2, $scope.filterParts).then(function (data) {
                if ($scope.choosenTypeID != null) {
                    var dataSend = {};
                    dataSend.attrID = 2;
                    dataSend.optID = $scope.choosenTypeID;
                    $scope.alternativePapers = [];
                    AttributeFiltersService.getRelativePapers(dataSend).then(function(altPapersFilter){
                        if(altPapersFilter.length > 0){
                            var filterPartsAltPapers = [];
                            filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'name', 'text', filterConfig, 'name_of_atrritute');
                            filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'category', 'select', filterConfig);
                            filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'group', 'select', filterConfig);
                            filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'paper_type', 'select', filterConfig);
                            filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'weight', 'range', filterConfig, null, false, 0);
                            filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'whiteness', 'range', filterConfig, null, false, 0);
                            filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'thickness', 'range', filterConfig, null, false, 3);
                            filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'opacity', 'range', filterConfig, null, false, 0);
                            filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'roughness', 'range', filterConfig, null, false, 0);
                            filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'certificates', 'multi-select', filterConfig);
                            filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'printingTechniques', 'multi-select', filterConfig);
                            filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'application', 'multi-select', filterConfig);
                            filterPartsAltPapers = createFilterPart(filterPartsAltPapers, 'color_hex', 'multi-select-color', filterConfig, 'paper_color');
                            _.each(altPapersFilter, function (fd) {
                                var part = _.find(filterPartsAltPapers, {name: fd.name});
                                if (fd.valueType == 'min') {
                                    part.minValue = fd.value;
                                } else if (fd.valueType == 'max') {
                                    part.maxValue = fd.value;
                                } else if (part.type == 'multi-select' || part.type == 'multi-select-color') {
                                    if (!part.selectedValues) {
                                        part.selectedValues = [];
                                    }
                                    part.selectedValues[fd.value] = true;
                                }  else if (fd.valueType == 'exact') {
                                    part.value = String(fd.value);
                                }
                            });
                            AttributeFiltersService.search(2, filterPartsAltPapers).then(function (altPapers) {
                                $scope.alternativePapers = altPapers;
                            });
                        }
                    });
                }
                // agregateIDSFilter
                if(agregateIDSFilter.length === 0){
                    $scope.filteredOptions = data;
                }else{
                    $scope.filteredOptions = _.filter(data, function (singleData) {
                        if(agregateIDSFilter.includes(singleData.ID)){
                            return true;
                        }else{
                            return false;
                        }
                    });
                }

                if ($scope.currentDisplayPapersType === 'default') {
                    $scope.currentDisplayPapersPage = 1;
                    var arrayStart = 0;
                    var arrayEnd = papersPerPage * $scope.currentDisplayPapersPage;
                    $scope.currentDisplayPapersPageData = $scope.filteredOptions.slice(arrayStart, arrayEnd);
                    preparePagination();
                }

                var filteredOptionsIds = _.map($scope.filteredOptions, function (item) {
                    return item.ID;
                });

                $scope.products = _.filter(allProductsUsingOptions, function (product) {
                    for (var i = 0; i < product.options.length; i++) {
                        if ($scope.choosenTypeID != null) {
                            if (product.options[i] == $scope.choosenTypeID) {
                                return true;
                            }
                        } else {
                            for (var j = 0; j < filteredOptionsIds.length; j++) {
                                if (product.options[i] == filteredOptionsIds[j]) {
                                    return true;
                                }
                            }
                        }
                    }
                    return false;
                });
            }, function (error) {
            });
        }

        // $scope.onInputChange = function () {
        //     $scope.filtersUsed = true;
        //     var matchIds = ['ids'];
        //     var matchPart = ['name'];
        //     var matchRangeSlider = ['weight', 'whiteness', 'thickness', 'opacity', 'roughness'];
        //     var matchArrays = ['certificates', 'printingTechniques', 'color_hex', 'application'];
        //     $scope.filteredOptions = _.filter(allOptions, function (item) {
        //         var pass = true;
        //         for (var part in $scope.filterParts) {
        //             var filterValue = $scope.filterParts[part].value
        //             if (matchIds.indexOf($scope.filterParts[part].name) > -1 && filterValue) {
        //                 pass = filterValue.indexOf(item.ID) > -1;
        //             } else if (matchPart.indexOf($scope.filterParts[part].name) > -1 && filterValue) {
        //                 pass = item.names[$rootScope.currentLang.code] && item.names[$rootScope.currentLang.code].toLowerCase().indexOf(filterValue.toLowerCase()) > -1;
        //             } else if (matchRangeSlider.indexOf($scope.filterParts[part].name) > -1 && item.descriptions[$scope.filterParts[part].name]) {
        //                 var description = item.descriptions[$scope.filterParts[part].name];
        //                 pass = description >= $scope.filterParts[part].minValue && description <= $scope.filterParts[part].maxValue;
        //             } else if (matchArrays.indexOf($scope.filterParts[part].name) > -1) {
        //                 var filterValues = [];
        //                 for (var key in $scope.filterParts[part].selectedValues) {
        //                     if ($scope.filterParts[part].selectedValues[key]) {
        //                         filterValues.push(key);
        //                     }
        //                 }
        //                 if (filterValues.length > 0) {
        //                     var xor = _.xor(filterValues, item.descriptions[$scope.filterParts[part].name])
        //                     pass = xor && xor.length != (filterValues.length + item.descriptions[$scope.filterParts[part].name].length)
        //                 }
        //             }
        //             if (!pass) {
        //                 break;
        //             }
        //         }
        //         return pass;
        //     });

        //     if ($scope.currentDisplayPapersType === 'default') {
        //         $scope.currentDisplayPapersPage = 1;
        //         var arrayStart = 0;
        //         var arrayEnd = papersPerPage * $scope.currentDisplayPapersPage;
        //         $scope.currentDisplayPapersPageData = $scope.filteredOptions.slice(arrayStart, arrayEnd);
        //         preparePagination();
        //     }

        //     var filteredOptionsIds = _.map($scope.filteredOptions, function (item) {
        //         return item.ID;
        //     });

        //     console.log('$scope.choosenTypeID');
        //     console.log($scope.choosenTypeID);
        //     $scope.products = _.filter(allProductsUsingOptions, function (product) {
        //         for (var i = 0; i < product.options.length; i++) {
        //             if($scope.choosenTypeID != null){
        //                 if (product.options[i] == $scope.choosenTypeID) {
        //                     return true;
        //                 }
        //             }else{
        //                 for (var j = 0; j < filteredOptionsIds.length; j++) {
        //                     if (product.options[i] == filteredOptionsIds[j]) {
        //                         return true;
        //                     }
        //                 }
        //             }
        //         }
        //         return false;
        //     });
        // }

        $scope.onPageChange = function (page) {
            var numberOfPages = Math.ceil($scope.filteredOptions.length / papersPerPage);
            if (page < 1) {
                page = 1;
            } else if (page > numberOfPages) {
                page = numberOfPages;
            }
            var currentPage = page - 1;
            $scope.currentDisplayPapersPage = page;
            var arrayStart = currentPage * papersPerPage;
            var arrayEnd = papersPerPage * (currentPage + 1);
            $scope.currentDisplayPapersPageData = $scope.filteredOptions.slice(arrayStart, arrayEnd);
            preparePagination();
        };

        function preparePagination() {
            var numberOfPages = Math.ceil($scope.filteredOptions.length / papersPerPage);
            $scope.currentDisplayPapersPages = [];
            if(numberOfPages > $scope.numberOfPagesInPagination){
                var paginationPageStart = $scope.currentDisplayPapersPage - 3;
                while (paginationPageStart <= 0) {
                    paginationPageStart++;
                }
                while (paginationPageStart + $scope.numberOfPagesInPagination > numberOfPages) {
                    paginationPageStart--;
                }
                for (var i = paginationPageStart; i <= paginationPageStart + $scope.numberOfPagesInPagination; i++) {
                    $scope.currentDisplayPapersPages.push(i);
                }
            }else{
                for (var i = 1; i <= numberOfPages; i++) {
                    $scope.currentDisplayPapersPages.push(i);
                }
            }
        }

        $scope.onColorClick = function (unit, value) {
            if (value) {
                unit.selectedValues[value] = !unit.selectedValues[value];
            } else {
                unit.selectedValues = {};
            }

            $scope.onInputChange();
        }

        $scope.onCategoryClick = function (category) {
            $scope.filteredOptions = []
            $scope.visibleSection[category] = !$scope.visibleSection[category];
        }

        $scope.onGroupClick = function (group) {
            $scope.visibleSection[group] = !$scope.visibleSection[group];
        }

        $scope.onTypeClick = function (category, group, type, data) {
            var options = $scope.categoriesTree[category][group][type];
            $scope.typeName = type;
            $scope.typeDescription = options.description;
            $scope.typeIcon = options.image;
            var tmpIDS = data.IDS;
            agregateIDSFilter = tmpIDS;
            $scope.onInputChange();
        }

        $scope.withUnit = function (value, unit) {
            if (!value) {
                return '-';
            }
            return value + ' ' + unit
        }

        $scope.resetCatTree = function () {
            $scope.visibleSection = {};
            $scope.typeIcon = $scope.typeDescription = null;
            agregateIDSFilter = [];
            $scope.onInputChange();
        }

        $scope.resetFilters = function () {
            $scope.currentDisplayPapersType = 'default';
            $scope.typeName = $scope.typeDescription = $scope.typeIcon = '';
            $scope.resetCatTree();
            _.each($scope.filterParts, function (unit) {
                unit.selectedValues = {};
                unit.value = null;
                if (unit.type == 'range') {
                    var part = _.find(filterParts, { name: unit.name });
                    unit.minValue = part.minValue;
                    unit.maxValue = part.maxValue;
                }
            })
            $scope.onInputChange();
        }
    });

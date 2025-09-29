'use strict';

angular.module('digitalprint.services')
    .factory('DomWidgetService', function () {

        const DomWidgetService = {};

        function pinElementWhenScroll(mainSelector, positionSelector, widthSelector) {
            const wrap = document.querySelector(mainSelector);
            const configWrap = document.querySelector(widthSelector);
            const panelHeading = document.querySelector(positionSelector);

            // Sprawdzenie krytycznych elementów
            if (!wrap || !panelHeading) {
                console.warn('Brakuje jednego lub więcej elementów DOM krytycznych:', {
                    wrap: wrap,
                    panelHeading: panelHeading
                });
                return;
            }

            // Ustawienie wrapWidth z alternatywą, gdy configWrap nie istnieje
            let wrapWidth = configWrap ? configWrap.clientWidth : wrap.clientWidth;
            const position = getPosition(panelHeading);

            $(window).on("scroll", function() {
                if (!wrap) return;

                if (this.scrollY > position.y) {
                    addClass(wrap, "fix-panel");
                    wrap.style.width = wrapWidth + 'px';
                } else {
                    removeClass(wrap, "fix-panel");
                    wrap.style.width = 'auto';
                }
            });

            $(window).on('resize', function () {
                if (!wrap) return;

                // Ponowne sprawdzenie configWrap przy zmianie rozmiaru
                wrapWidth = configWrap ? configWrap.clientWidth : wrap.clientWidth;
                if (this.scrollY > position.y) {
                    wrap.style.width = wrapWidth + 'px';
                }
            });
        }

        function getPosition(element) {
            let xPosition = 0;
            let yPosition = 0;

            // Sprawdzenie, czy element istnieje
            if (!element) {
                return { x: xPosition, y: yPosition };
            }

            while (element) {
                xPosition += (element.offsetLeft - element.scrollLeft + element.clientLeft);
                yPosition += (element.offsetTop - element.scrollTop + element.clientTop);
                element = element.offsetParent;
            }

            return { x: xPosition, y: yPosition };
        }

        function hasClass(element, existClass) {
            return !!element.className.match(new RegExp('(\\s|^)' + existClass + '(\\s|$)'));
        }

        function addClass(element, newClass) {
            if (!hasClass(element, newClass)) element.className += " " + newClass;
        }

        function removeClass(element, existClass) {
            if (hasClass(element, existClass)) {
                const reg = new RegExp('(\\s|^)' + existClass + '(\\s|$)');
                element.className = element.className.replace(reg, ' ');
            }
        }

        return {
            pinElementWhenScroll: pinElementWhenScroll
        };
    });

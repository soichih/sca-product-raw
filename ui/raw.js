(function() {
    'use strict';

    //https://github.com/danialfarid/ng-file-upload
    var service = angular.module('sca-product-raw', [ ]);
    service.directive('scaProductRaw', function(toaster, $http, $timeout, scaTask, appconf) {
        return {
            restrict: 'E',
            scope: {
                taskid: '<',
                path: '=?', //if empty, it will be set to instantce_id / task_id (relative to task dir)
            }, 
            templateUrl: 'node_modules/sca-product-raw/ui/raw.html',
            controller: function($scope) {
                function load_resource(resource_id) {
                    if(!resource_id) return;
                    //load resource detail
                    console.log("loading resource detail:"+resource_id);
                    $http.get(appconf.wf_api+"/resource/", {
                        params: {
                            find: JSON.stringify({ _id: resource_id })
                        }
                    }).then(function(res) {
                        if(res.data.resources && res.data.resources.length == 1) {
                            //console.log("loaded resource details");
                            //console.dir(res.data.resources);
                            $scope.resource_detail = res.data.resources[0];
                        } else {
                            console.error("couldn't load resource detail: ");
                        }
                    }, function(res) {
                        if(res.data && res.data.message) toaster.error(res.data.message);
                        else toaster.error(res.statusText);
                    });
                }
                
                //need to load task so that I can load resource
                var t = scaTask.get($scope.taskid);
                t._promise.then(function() {
                    $scope.task = t;
                    $scope.$watch('task.resource_id', function() {          
                        //console.log("task.resource_id updated:"+t.resource_id);
                        load_resource(t.resource_id);
                    });
                });
            }
        };
    });

    service.component('scaProductRawDir', {
        //transclude: true,
        bindings: {
            taskid: '=',
            indent: '=',
            path: '=?', //if empty, it will be set to instantce_id / task_id (relative to task dir)
        },
        templateUrl: 'node_modules/sca-product-raw/ui/dir.html',
        controller: function($scope, appconf, $http, toaster, scaTask) {
            console.log("loading directory");
            var $ctrl = this;
            var jwt = localStorage.getItem(appconf.jwt_id);
            this.indent_child = this.indent+1;
            if(!this.path) this.path = "";

            this.getNumber = function(num) { return new Array(num); };

            //start by loading task
            var t = scaTask.get(this.taskid);
            t._promise.then(function() {
                $ctrl.taskdir = t.instance_id+"/"+t._id;
                if(!t.resource_id) {
                    console.error("sca-product-raw initialized on task with no resource_id");
                    return;
                }

                $ctrl.loading = true;
                console.log("ls resource:"+t.resource_id+" path:"+$ctrl.taskdir+"/"+$ctrl.path);
                $http.get(appconf.wf_api+"/resource/ls/"+t.resource_id, {
                    //timeout: 3000, //server side should handle this (with good explanation)
                    params: { path: $ctrl.taskdir+"/"+$ctrl.path }
                })
                .then(function(res) {
                    $ctrl.loading = false;
                    $ctrl.files = res.data.files;
                    $ctrl.files.forEach(function(file) {
                        file.path = $ctrl.path+"/"+file.filename;
                        file.url = appconf.wf_api+"/resource/download?r="+t.resource_id+"&p="+encodeURIComponent($ctrl.taskdir+"/"+file.path)+"&at="+jwt;
                    });
                    console.dir($ctrl.files);
                }, function(res) {
                    $ctrl.loading = false;

                    //ls could fail if taskdir isn't setup yet (or task starup fails).. so let's not display this to the UI
                    console.log("ls failed");
                    console.dir(res);
                    //if(res.data && res.data.message) toaster.error(res.data.message);
                    //else toaster.error(res.statusText);
                });

            });

            /*
            $scope.link = function(file) {
                console.dir(file);
                alert("Traversing symbolic link is currently disabled");
            }
            */
            $scope.click = function(file) {
                switch(file.attrs.mode_string[0]) {
                case "d":
                    file.open = !file.open; break;
                case "l":
                    alert("Traversing symbolic link is currently disabled");
                    break;
                case "-":
                    window.location = file.url;
                }
                console.dir(file);
            }
        }
    });

    //can't quite do the slidedown animation through pure angular/css.. borrowing slideDown from jQuery..
    service.animation('.slide-down', ['$animateCss', function($animateCss) {
        return {
            enter: function(elem, done) {
                $(elem).hide().slideDown("normal", done);
            },
            leave: function(elem, done) {
                $(elem).slideUp("normal", done);
            }
        };
    }]);

    service.filter('bytes', function() {
        return function(bytes, precision) {
            if (isNaN(parseFloat(bytes)) || !isFinite(bytes)) return '-';
            if (typeof precision === 'undefined') precision = 1;
            var units = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'],
                number = Math.floor(Math.log(bytes) / Math.log(1024));
            return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) +  ' ' + units[number];
        }
    });

    service.filter('encodeURI', function() {
      return window.encodeURIComponent;
    });
        
    //end of IIFE (immediately-invoked function expression)
})();



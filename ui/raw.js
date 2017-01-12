(function() {
    'use strict';

    //https://github.com/danialfarid/ng-file-upload
    var service = angular.module('sca-product-raw', [ ]);
    service.directive('scaProductRaw', function(toaster, $http, $timeout, scaTask, appconf) {
        return {
            restrict: 'E',
            scope: {
                taskid: '=',
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

    service.directive('scaProductRawDir', function(appconf, $http, toaster, scaTask) {
        return {
            restrict: 'E',
            scope: {
                taskid: '=',
                indent: '=',
                path: '=?', //if empty, it will be set to instantce_id / task_id (relative to task dir)
            },
            templateUrl: 'node_modules/sca-product-raw/ui/dir.html',
            controller: function($scope) {
                console.log("loading directory taskid:"+$scope.taskid);
                $scope.indent_child = $scope.indent+1;
                if(!$scope.path) $scope.path = "";

                this.getNumber = function(num) { return new Array(num); };

                //start by loading task
                var task = scaTask.get($scope.taskid);
                task._promise.then(function() {
                    //console.log("scaTask.get returned task");
                    //console.log(JSON.stringify(task));
                    $scope.taskdir = task.instance_id+"/"+task._id;
                    if(!task.resource_id) {
                        console.error("sca-product-raw initialized on task with no resource_id");
                        return;
                    }

                    $scope.loading = true;
                    //console.log("ls resource:"+task.resource_id+" path:"+$scope.taskdir+"/"+$scope.path);
                    $http.get(appconf.wf_api+"/resource/ls/"+task.resource_id, {
                        params: { path: $scope.taskdir+"/"+$scope.path }
                    })
                    .then(function(res) {
                        $scope.loading = false;
                        $scope.files = res.data.files;
                        var jwt = localStorage.getItem(appconf.jwt_id);
                        $scope.files.forEach(function(file) {
                            file.path = $scope.path+"/"+file.filename;
                            file.url = appconf.wf_api+"/resource/download?r="+task.resource_id+
                                "&p="+encodeURIComponent($scope.taskdir+"/"+file.path)+
                                "&at="+jwt;
                        });
                        $scope.error = null;
                        //console.dir($scope.files);
                    }, function(res) {
                        $scope.loading = false;
                        //ls could fail if taskdir isn't setup yet (or task starup fails).. so let's not display this to the UI
                        //console.log("ls failed");
                        //console.dir(res);
                        if(res.data && res.data.message) $scope.error = res.data.message;
                        //if(res.data && res.data.message) toaster.error(res.data.message);
                        //else toaster.error(res.statusText);
                    });
                });

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
                }
            }
        };
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

    /* should come from sca-ng-wf
    service.filter('bytes', function() {
        return function(bytes, precision) {
            if (isNaN(parseFloat(bytes)) || !isFinite(bytes)) return '-';
            if (typeof precision === 'undefined') precision = 1;
            var units = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'],
                number = Math.floor(Math.log(bytes) / Math.log(1024));
            return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) +  ' ' + units[number];
        }
    });
    */

    service.filter('encodeURI', function() {
      return window.encodeURIComponent;
    });
        
    //end of IIFE (immediately-invoked function expression)
})();



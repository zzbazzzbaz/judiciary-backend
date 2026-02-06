/**
 * Task 表单：网格字段联动过滤人员 autocomplete 下拉框。
 *
 * 功能：
 * 1. 选择「所属网格」后，上报人/分配人/被分配调解员的 autocomplete 搜索自动携带 grid_id 参数
 * 2. 切换网格时，自动清空已选的人员（因为原来选的人可能不在新网格内）
 */
(function($) {
    'use strict';

    if (!$) return;

    // ========== 1. 拦截 autocomplete AJAX 请求，注入 grid_id ==========
    $.ajaxPrefilter(function(options) {
        // 只处理 autocomplete 请求
        if (!options.url || options.url.indexOf('/autocomplete/') === -1) return;

        var gridEl = document.getElementById('id_grid');
        if (!gridEl || !gridEl.value) return;

        // 将 grid_id 追加到请求数据中
        if (typeof options.data === 'string') {
            options.data += '&grid_id=' + encodeURIComponent(gridEl.value);
        } else if (options.data && typeof options.data === 'object') {
            options.data.grid_id = gridEl.value;
        } else {
            options.data = 'grid_id=' + encodeURIComponent(gridEl.value);
        }
    });

    // ========== 2. 网格变更时清空人员选择 ==========
    var USER_FIELDS = ['reporter', 'assigner', 'assigned_mediator'];

    function clearUserSelections() {
        USER_FIELDS.forEach(function(field) {
            var $field = $('#id_' + field);
            if ($field.length) {
                $field.val(null).trigger('change');
            }
        });
    }

    function bindGridChange() {
        var $grid = $('#id_grid');
        if (!$grid.length) return;

        $grid.on('change', function() {
            clearUserSelections();
        });
    }

    // DOM ready
    $(function() {
        bindGridChange();
    });

})(django.jQuery || jQuery);

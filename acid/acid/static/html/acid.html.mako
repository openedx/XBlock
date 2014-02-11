<div class="acid-block"
    data-success-class="${success_class}"
    data-failure-class="${failure_class}"
    data-error-class="${error_class}"
    data-unknown-class="${unknown_class}"
    data-acid-child-values='${acid_child_values}'
    data-acid-child-count="${acid_child_count}"
    >

    <p>Acid XBlock</p>
    <p>JS init function run:
        <span class="js-init-run">
            <i class="${unknown_class}"></i>
        </span>
    </p>
    <p>Document-ready function run:
        <span class="document-ready-run">
            <i class="${unknown_class}"></i>
        </span>
    </p>
    <p>Acid Child counts match:
        <span class="child-counts-match">
            <i class="${unknown_class}"></i>
        </span>
    </p>
    <p>Acid Child values match:
        <span class="child-values-match">
            <i class="${unknown_class}"></i>
        </span>
    </p>
    <table class='storage-tests'>
        <tr>
            <th>Scope</th>
            <th>Server-side<br>handler_url<br>returned</th>
            <th>Server-side<br>handler_url<br>succeeded</th>
            <th>Client-side<br>handler_url<br>returned</th>
            <th>Client-side<br>handler_url<br>succeeded</th>
        </tr>
        % for test in storage_tests:
            <tr class="scope-storage-test scope-{scope} ${loop.cycle('', 'alt')}"
                data-handler-url="${test['handler_url']}"
                data-scope="${test['scope']}"
                data-value="${test['value']}"
            >
                <td>${test['scope']}</td>
                <td>
                    <span class="server-storage-test-returned">
                        <i class="${unknown_class}"></i>
                    </span>
                </td>
                <td>
                    <span class="server-storage-test-succeeded">
                        <i class="${unknown_class}"></i>
                    </span>
                </td>
                <td>
                    <span class="client-storage-test-returned">
                        <i class="${unknown_class}"></i>
                    </span>
                </td>
                <td>
                    <span class="client-storage-test-succeeded">
                        <i class="${unknown_class}"></i>
                    </span>
                </td>
            </tr>
        % endfor
    </table>
    <div class='acid-children'>
        % for child in rendered_children:
            ${child}
        % endfor
    </div>
</div>

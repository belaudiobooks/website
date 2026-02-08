/**
 * Sales page DataTables initialization with ColumnControl filtering.
 * Supports monthly, yearly, and all-time view toggle.
 * Expects:
 * - #sales-data: JSON script element with sales data array
 * - #sales-config: JSON script element with DataTables language config
 * - #sales-table: Table element to initialize
 * - Radio buttons with name="view-toggle" for view selection
 */
document.addEventListener('DOMContentLoaded', function () {
    const salesDataEl = document.getElementById('sales-data');
    const configEl = document.getElementById('sales-config');
    const viewToggles = document.querySelectorAll('input[name="view-toggle"]');

    if (!salesDataEl || !configEl) return;

    const monthlyData = JSON.parse(salesDataEl.textContent);
    const config = JSON.parse(configEl.textContent);

    if (monthlyData.length === 0) return;

    let table = null;

    // Aggregate data by book only for all-time view
    function aggregateAllTime(data) {
        const grouped = {};
        data.forEach(function (row) {
            const key = row.book_slug;
            if (!grouped[key]) {
                grouped[key] = {
                    book_title: row.book_title,
                    book_slug: row.book_slug,
                    author: row.author,
                    quantity: 0,
                    original_amount: 0,
                    royalty_share: row.royalty_share,
                    payable_royalty: 0
                };
            }
            grouped[key].quantity += row.quantity;
            grouped[key].original_amount += row.original_amount;
            grouped[key].payable_royalty += row.payable_royalty;
        });
        return Object.values(grouped);
    }

    // Aggregate data by book and year for yearly view
    function aggregateByYear(data) {
        const grouped = {};
        data.forEach(function (row) {
            const key = row.book_slug + '|' + row.year;
            if (!grouped[key]) {
                grouped[key] = {
                    book_title: row.book_title,
                    book_slug: row.book_slug,
                    author: row.author,
                    year: row.year,
                    quantity: 0,
                    original_amount: 0,
                    royalty_share: row.royalty_share,
                    payable_royalty: 0
                };
            }
            grouped[key].quantity += row.quantity;
            grouped[key].original_amount += row.original_amount;
            grouped[key].payable_royalty += row.payable_royalty;
        });
        return Object.values(grouped);
    }

    // Common column definitions
    const bookColumn = {
        data: 'book_title',
        render: function (data, type, row) {
            if (type === 'display') {
                return '<a href="/books/' + row.book_slug + '/">' + data + '</a>';
            }
            return data;
        }
    };
    const authorColumn = { data: 'author' };
    const yearColumn = { data: 'year' };
    const monthColumn = {
        data: 'month_name',
        render: function (data, type, row) {
            if (type === 'sort') {
                return row.month;
            }
            return data;
        }
    };
    const quantityColumn = { data: 'quantity', className: 'text-end' };
    const originalAmountColumn = {
        data: 'original_amount',
        className: 'text-end',
        render: function (data, type) {
            if (type === 'display') {
                return '$' + data.toFixed(2);
            }
            return data;
        }
    };
    const royaltyShareColumn = {
        data: 'royalty_share',
        className: 'text-end',
        render: function (data, type) {
            if (type === 'display') {
                return data.toFixed(0) + '%';
            }
            return data;
        }
    };
    const payableRoyaltyColumn = {
        data: 'payable_royalty',
        className: 'text-end',
        render: function (data, type) {
            if (type === 'display') {
                return '$' + data.toFixed(2);
            }
            return data;
        }
    };

    // Footer callback generator
    function createFooterCallback(quantityIdx, payableRoyaltyIdx) {
        return function (row, data, start, end, display) {
            const api = this.api();

            const totalQuantity = api
                .column(quantityIdx, { search: 'applied' })
                .data()
                .reduce(function (a, b) { return a + b; }, 0);

            const totalPayableRoyalty = api
                .column(payableRoyaltyIdx, { search: 'applied' })
                .data()
                .reduce(function (a, b) { return a + b; }, 0);

            $(api.column(quantityIdx).footer()).text(totalQuantity);
            $(api.column(payableRoyaltyIdx).footer()).text('$' + totalPayableRoyalty.toFixed(2));
        };
    }

    // Monthly view configuration
    function getMonthlyConfig() {
        return {
            data: monthlyData,
            columns: [
                bookColumn,
                authorColumn,
                yearColumn,
                monthColumn,
                quantityColumn,
                originalAmountColumn,
                royaltyShareColumn,
                payableRoyaltyColumn
            ],
            order: [[2, 'desc'], [3, 'desc'], [0, 'asc']],
            pageLength: 25,
            language: config.language,
            columnControl: ['order', ['searchList', 'spacer', 'orderAsc', 'orderDesc', 'orderClear']],
            columnDefs: [
                { targets: [4, 5, 6, 7], columnControl: ['order'] }
            ],
            ordering: { handler: false, indicators: false },
            footerCallback: createFooterCallback(4, 7)
        };
    }

    // Yearly view configuration
    function getYearlyConfig() {
        return {
            data: aggregateByYear(monthlyData),
            columns: [
                bookColumn,
                authorColumn,
                yearColumn,
                quantityColumn,
                originalAmountColumn,
                royaltyShareColumn,
                payableRoyaltyColumn
            ],
            order: [[2, 'desc'], [0, 'asc']],
            pageLength: 25,
            language: config.language,
            columnControl: ['order', ['searchList', 'spacer', 'orderAsc', 'orderDesc', 'orderClear']],
            columnDefs: [
                { targets: [3, 4, 5, 6], columnControl: ['order'] }
            ],
            ordering: { handler: false, indicators: false },
            footerCallback: createFooterCallback(3, 6)
        };
    }

    // All-time view configuration
    function getAllTimeConfig() {
        return {
            data: aggregateAllTime(monthlyData),
            columns: [
                bookColumn,
                authorColumn,
                quantityColumn,
                originalAmountColumn,
                royaltyShareColumn,
                payableRoyaltyColumn
            ],
            order: [[0, 'asc']],
            pageLength: 25,
            language: config.language,
            columnControl: ['order', ['searchList', 'spacer', 'orderAsc', 'orderDesc', 'orderClear']],
            columnDefs: [
                { targets: [2, 3, 4, 5], columnControl: ['order'] }
            ],
            ordering: { handler: false, indicators: false },
            footerCallback: createFooterCallback(2, 5)
        };
    }

    // View modes
    const VIEW_ALL_TIME = 'all-time';
    const VIEW_YEARLY = 'yearly';
    const VIEW_MONTHLY = 'monthly';

    // Initialize or reinitialize table
    function initTable(viewMode) {
        if (table) {
            table.destroy();
        }

        const labels = config.labels;

        // Rebuild header
        const thead = document.querySelector('#sales-table thead tr');
        if (viewMode === VIEW_ALL_TIME) {
            thead.innerHTML = `
                <th scope="col">${labels.book}</th>
                <th scope="col">${labels.author}</th>
                <th scope="col" class="text-end">${labels.quantity}</th>
                <th scope="col" class="text-end">${labels.originalAmount}</th>
                <th scope="col" class="text-end">${labels.royaltyShare}</th>
                <th scope="col" class="text-end">${labels.payableRoyalty}</th>
            `;
        } else if (viewMode === VIEW_YEARLY) {
            thead.innerHTML = `
                <th scope="col">${labels.book}</th>
                <th scope="col">${labels.author}</th>
                <th scope="col">${labels.year}</th>
                <th scope="col" class="text-end">${labels.quantity}</th>
                <th scope="col" class="text-end">${labels.originalAmount}</th>
                <th scope="col" class="text-end">${labels.royaltyShare}</th>
                <th scope="col" class="text-end">${labels.payableRoyalty}</th>
            `;
        } else {
            thead.innerHTML = `
                <th scope="col">${labels.book}</th>
                <th scope="col">${labels.author}</th>
                <th scope="col">${labels.year}</th>
                <th scope="col">${labels.month}</th>
                <th scope="col" class="text-end">${labels.quantity}</th>
                <th scope="col" class="text-end">${labels.originalAmount}</th>
                <th scope="col" class="text-end">${labels.royaltyShare}</th>
                <th scope="col" class="text-end">${labels.payableRoyalty}</th>
            `;
        }

        // Rebuild footer
        const tfoot = document.querySelector('#sales-table tfoot tr');
        if (viewMode === VIEW_ALL_TIME) {
            tfoot.innerHTML = `
                <td>${labels.total}</td>
                <td></td>
                <td class="text-end" data-test-id="total-quantity">0</td>
                <td></td>
                <td></td>
                <td class="text-end" data-test-id="total-payable-royalty">$0.00</td>
            `;
        } else if (viewMode === VIEW_YEARLY) {
            tfoot.innerHTML = `
                <td>${labels.total}</td>
                <td></td>
                <td></td>
                <td class="text-end" data-test-id="total-quantity">0</td>
                <td></td>
                <td></td>
                <td class="text-end" data-test-id="total-payable-royalty">$0.00</td>
            `;
        } else {
            tfoot.innerHTML = `
                <td>${labels.total}</td>
                <td></td>
                <td></td>
                <td></td>
                <td class="text-end" data-test-id="total-quantity">0</td>
                <td></td>
                <td></td>
                <td class="text-end" data-test-id="total-payable-royalty">$0.00</td>
            `;
        }

        // Clear tbody
        document.querySelector('#sales-table tbody').innerHTML = '';

        let tableConfig;
        if (viewMode === VIEW_ALL_TIME) {
            tableConfig = getAllTimeConfig();
        } else if (viewMode === VIEW_YEARLY) {
            tableConfig = getYearlyConfig();
        } else {
            tableConfig = getMonthlyConfig();
        }
        table = new DataTable('#sales-table', tableConfig);
    }

    // Get view mode from radio button id
    function getViewModeFromId(id) {
        if (id === 'view-all-time') return VIEW_ALL_TIME;
        if (id === 'view-yearly') return VIEW_YEARLY;
        return VIEW_MONTHLY;
    }

    // Initialize with all-time view (default)
    initTable(VIEW_ALL_TIME);

    // Handle toggle
    viewToggles.forEach(function (toggle) {
        toggle.addEventListener('change', function () {
            if (this.checked) {
                initTable(getViewModeFromId(this.id));
            }
        });
    });
});

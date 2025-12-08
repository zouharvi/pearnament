import { notify } from "./utils"
import $ from 'jquery';

let searchParams = new URLSearchParams(window.location.search)

let campaign_ids = searchParams.getAll("campaign_id")
let tokens = searchParams.getAll("token")
let showResults = searchParams.has("results")

// verify that tokens length is either 0 or same as campaign_ids length
if (tokens.length != 0 && tokens.length != campaign_ids.length) {
    $("#main_div").html(`
        <div class="white-box">
        ⛔ Either no tokens should be provided or the same number as campaign IDs.
        </div>
    `)
    throw new Error("Mismatched number of tokens and campaign IDs")
}

function delta_to_human(delta: number): string {
    /* Convert a time delta in seconds to a human-readable format */
    if (delta < 60) {
        return `${Math.round(delta)}s`
    } else if (delta < 60 * 60) {
        return `${Math.round(delta / 60)}m`
    } else if (delta < 60 * 60 * 24) {
        return `${Math.round(delta / 60 / 60)}h`
    } else {
        return `${Math.round(delta / 60 / 60 / 24)}d`
    }
}

async function fetchAndRenderCampaign(campaign_id: string, token: string | null) {
    let x = await $.ajax({
        url: `/dashboard-data`,
        method: "POST",
        data: JSON.stringify({ "campaign_id": campaign_id, "token": token }),
        contentType: "application/json",
        dataType: "json",
    });
    let data = x.data;

    // Fetch results if requested and token is available
    let resultsData = null;
    if (showResults && token !== null && token !== undefined) {
        try {
            resultsData = await $.ajax({
                url: `/dashboard-results`,
                method: "POST",
                data: JSON.stringify({ "campaign_id": campaign_id, "token": token }),
                contentType: "application/json",
                dataType: "json",
            });
        } catch (error) {
            console.error("Error fetching results:", error);
        }
    }

    let html = ""
    html += `
    <table class="dashboard-table">
        <thead><tr>
            <th style="min-width: 300px;">User ID</th>
            <th style="min-width: 50px;">Progress</th>
            <th style="min-width: 80px;">First</th>
            <th style="min-width: 80px;">Last</th>
            <th style="min-width: 80px;">Time</th>
            <th style="min-width: 70px;">Checks</th>
            <th style="min-width: 50px;">Actions</th>
        </tr></thead>
        <tbody>`
    for (let user_id in data) {
        // sum
        let progress_count = (data[user_id]["progress"] as Array<boolean>).reduce((a, b) => a + (b ? 1 : 0), 0)
        let progress_total = (data[user_id]["progress"] as Array<boolean>).length
        let failed_checks = data[user_id]["failed_checks"] || 0
        let threshold_passed = data[user_id]["threshold_passed"]
        let status = ''
        if (data[user_id]["time"] == 0)
            status = '💤'
        else if (data[user_id]["time"] != 0 && progress_count == progress_total) {
            // Use threshold_passed to determine if user passed/failed
            // threshold_passed is null if not complete, true if passed, false if failed
            if (threshold_passed === false)
                status = '❌'
            else
                status = '✅'
        }
        else
            status = '✍️'

        html += '<tr>'

        // user id and emoji
        html += `<td>${status} ${user_id}</td>`

        // time section
        html += `<td>${progress_count}/${progress_total}</td>`
        if (data[user_id]["time_start"] == null) {
            html += `<td title="N/A"></td>`
        } else {
            html += `<td title="${new Date(data[user_id]["time_start"] * 1000).toLocaleString()}">${delta_to_human(Date.now() / 1000 - data[user_id]["time_start"])} ago</td>`
        }
        if (data[user_id]["time_end"] == null) {
            html += `<td title="N/A"></td>`
        } else {
            html += `<td title="${new Date(data[user_id]["time_end"] * 1000).toLocaleString()}">${delta_to_human(Date.now() / 1000 - data[user_id]["time_end"])} ago</td>`
        }
        html += `<td>${Math.round(data[user_id]["time"] / 60)}m</td>`

        let validation_passed = data[user_id]["validations"].reduce((a: number, b: boolean) => a + (b ? 1 : 0), 0)
        let validation_total = data[user_id]["validations"].length
        html += `<td><span style="${validation_passed != validation_total ? 'color: #c75050;' : ''}">${validation_passed}</span><span style="color: #333;">/${validation_total}</span></td>`

        // actions section
        html += `<td>
            <a href="${data[user_id]["url"]}">🔗</a>
            &nbsp;&nbsp;
            <a href="${data[user_id]["url"]}&frozen" title="View only (frozen)">👁️</a>
            &nbsp;&nbsp;
            <span class="reset-task" user_id="${user_id}" ${token == null ? "disabled" : ""}>🗑️</span>
        </td>`
        html += '</tr>'
    }
    html += '</tbody></table>'

    // Add results section if available
    let resultsHtml = '';
    if (resultsData && resultsData.length > 0) {
        resultsHtml = `
        <div class="results-section">
            <h4 style="margin-top: -2.5em;">Intermediate results</h4>
            <table class="results-table">
                <thead><tr>
                    <th>Model</th>
                    <th>Score</th>
                    <th>Count</th>
                </tr></thead>
                <tbody>`;
        
        for (let result of resultsData) {
            resultsHtml += `
                <tr>
                    <td>${result.model}</td>
                    <td>${result.score.toFixed(1)}</td>
                    <td>${result.count}</td>
                </tr>`;
        }
        
        resultsHtml += `
                </tbody>
            </table>
        </div>`;
    }

    // link to campaign-specific dashboard
    let dashboard_url = `${window.location.origin}/dashboard.html?campaign_id=${encodeURIComponent(campaign_id)}${token != null ? `&token=${encodeURIComponent(token)}` : ''}${showResults ? '&results' : ''}`
    let el = $(`
        <div class="white-box">
        <h3>${campaign_id} <a href="${dashboard_url}">🔗</a></h3>
        <div class="dashboard-content">
            ${html}
            ${resultsHtml}
        </div>
        </div>`)

    $("#dashboard_div").append(el)
    if (token != null) {
        el.find(".reset-task").on("click", function () {
            let user_id = $(this).attr("user_id")
            // show dialog to confirm
            if (!confirm(`Are you sure you want to reset progress for user ${$(this).attr("user_id")} in ${campaign_id}?\n\nThe user will annotate new data which will be stored alongside the already-collected data. This action cannot be undone.`)) {
                return
            }
            $.ajax({
                url: `/reset-task`,
                method: "POST",
                data: JSON.stringify({ "campaign_id": campaign_id, "user_id": user_id, "token": token }),
                contentType: "application/json",
                dataType: "json",
                success: (x) => {
                    notify(`Task for user ${user_id} has been reset.`)
                    location.reload()
                },
                error: (XMLHttpRequest) => {
                    const errorMsg = XMLHttpRequest.responseJSON?.error || XMLHttpRequest.responseText || XMLHttpRequest.statusText || "An unknown error occurred";
                    notify("Error resetting task: " + errorMsg);
                },
            });
        })
    }
}

// for each campaign_id, fetch dashboard data and display them in a white-box
(async () => {
    for (let i = 0; i < campaign_ids.length; i++) {
        let campaign_id = campaign_ids[i];
        let token = tokens[i] || null
        try {
            await fetchAndRenderCampaign(campaign_id, token);
        } catch (error: any) {
            const errorMsg = error?.responseJSON?.error || error?.responseText || error?.statusText || "An unknown error occurred";
            notify("Error fetching data: " + errorMsg);
        }
    }
})();


// progress requries an access token
if (tokens.length == 0) {
    $("#download_progress").attr("disabled", "true")
} else {
    $("#download_progress").attr("href", `/download-progress?${campaign_ids.map((id, i) => `campaign_id=${encodeURIComponent(id)}&${tokens[i] ? `token=${encodeURIComponent(tokens[i])}` : ''}`).join('&')}`)
}
$("#download_annotations").attr("href", `/download-annotations?${campaign_ids.map((id, i) => `campaign_id=${encodeURIComponent(id)}&${tokens[i] ? `token=${encodeURIComponent(tokens[i])}` : ''}`).join('&')}`)
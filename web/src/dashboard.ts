import { notify } from "./utils"
import $ from 'jquery';

let searchParams = new URLSearchParams(window.location.search)

let campaign_ids = searchParams.getAll("campaign_id")
let tokens = searchParams.getAll("token")

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

// for each campaign_id, fetch dashboard data and display them in a white-box
campaign_ids.forEach(async (campaign_id, i) => {
    let token = tokens[i] || null
    await $.ajax({
        url: `/dashboard-data`,
        method: "POST",
        data: JSON.stringify({ "campaign_id": campaign_id, "token": token }),
        contentType: "application/json",
        dataType: "json",
        success: (x) => {
            let data = x.data

            let html = ""
            html += `
                <table>
                    <thead><tr>
                        <th style="min-width: 300px;">User ID</th>
                        <th style="min-width: 50px;">Progress</th>
                        <th style="min-width: 80px;">First</th>
                        <th style="min-width: 80px;">Last</th>
                        <th style="min-width: 80px;">Time</th>
                        <th style="min-width: 50px;">Failed</th>
                        <th style="min-width: 50px;">Actions</th>
                    </tr></thead>
                    <tbody>`
            for (let user_id in data) {
                // sum
                let progress_count = (data[user_id]["progress"] as Array<boolean>).reduce((a, b) => a + (b ? 1 : 0), 0)
                let progress_total = (data[user_id]["progress"] as Array<boolean>).length
                let failed_checks = data[user_id]["failed_checks"] || 0
                let status = ''
                if (data[user_id]["time"] == 0)
                    status = '💤'
                else if (data[user_id]["time"] != 0 && progress_count == progress_total)
                    status = '✅'
                else
                    status = '🚧'

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
                
                // failed checks column
                html += `<td style="${failed_checks > 0 ? 'color: red; font-weight: bold;' : ''}">${failed_checks > 0 ? failed_checks : '-'}</td>`

                // actions section
                html += `<td>
                        <a href="${data[user_id]["url"]}">🔗</a>
                        &nbsp;&nbsp;
                        <span class="reset-task" user_id="${user_id}" ${token == null ? "disabled" : ""}>🗑️</span>
                    </td>` 
                html += '</tr>'
            }
            html += '</tbody></table>'

            // link to campaign-specific dashboard
            let dashboard_url = `${window.location.origin}/dashboard.html?campaign_id=${encodeURIComponent(campaign_id)}${token != null ? `&token=${encodeURIComponent(token)}` : ''}`
            let el = $(`
                    <div class="white-box">
                    <h3>${campaign_id} <a href="${dashboard_url}">🔗</a></h3>
                    ${html}
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
                        error: (XMLHttpRequest, textStatus, errorThrown) => {
                            notify("Error resetting task:" + JSON.stringify(textStatus) + JSON.stringify(errorThrown));
                        },
                    });
                })
            }
        },
        error: (XMLHttpRequest, textStatus, errorThrown) => {
            notify("Error fetching data:" + JSON.stringify(textStatus) + JSON.stringify(errorThrown));
        },
    });
});


// progress requries an access token
if (tokens.length == 0) {
    $("#download_progress").attr("disabled", "true")
} else {
    $("#download_progress").attr("href", `/download-progress?${campaign_ids.map((id, i) => `campaign_id=${encodeURIComponent(id)}}`).join('&')}`)
}
$("#download_annotations").attr("href", `/download-annotations?${campaign_ids.map((id, i) => `campaign_id=${encodeURIComponent(id)}&${tokens[i] ? `token=${encodeURIComponent(tokens[i])}` : ''}`).join('&')}`)
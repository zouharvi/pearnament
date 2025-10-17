import { notify } from "./utils"
import $ from 'jquery';

export type Item = { "src_id": string, "src": string[], "sys_a": string, "out_a": string[], "sys_b": string, "out_b": string[] }


export async function get_next_pair(): Promise<Item> {
    let uid = "TODOTODO";


    let delay = 1
    while (true) {
        try {
            return await new Promise<Item>((resolve, reject) => {
              $.ajax({
                url: "http://127.0.0.1:8001/get-next",
                method: "POST",
                data: JSON.stringify({ "uid": uid }),
                contentType: "application/json",
                dataType: "json",
                success: resolve,
                error: (XMLHttpRequest, textStatus, errorThrown) => {
                    console.error("Error fetching data:", textStatus, errorThrown);
                    reject(`Status: ${XMLHttpRequest.status} Error: ${XMLHttpRequest.responseText}`);
                },
              });
            });
          } catch (e) {
            console.log("Error in try-catch:", e);
            notify(`Error fetching item. <br> ${e} <br> Retrying in ${delay} seconds...`);
          }
        // wait for 5 seconds
        await new Promise(resolve => setTimeout(resolve, delay * 1000));
        delay *= 2
    }
}
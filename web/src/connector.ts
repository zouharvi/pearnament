import { notify } from "./utils"
import $ from 'jquery';

export type Data = {"payload": { "src": Array<string>, "tgt": Array<string> }, "progress": {"completed": number, "total": number}, "time": number}
let searchParams = new URLSearchParams(window.location.search)

export async function get_next_item(): Promise<Data> {
  let user_id = searchParams.get("user_id");
  let campaign_id = searchParams.get("campaign_id");
  let server_url = searchParams.get("server_url");

  let delay = 1
  while (true) {
      try {
          return await new Promise<Data>((resolve, reject) => {
            $.ajax({
              url: `${server_url}/get-next-item`,
              method: "POST",
              data: JSON.stringify({ "campaign_id": campaign_id, "user_id": user_id }),
              contentType: "application/json",
              dataType: "json",
              // TODO: handle being done
              success: (x) => resolve(x),
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
    
    
    export async function log_response(payload: any): Promise<void> {
      let user_id = searchParams.get("user_id");
      let campaign_id = searchParams.get("campaign_id");
      let server_url = searchParams.get("server_url");
      
      let delay = 1
      while (true) {
        try {
          return await new Promise<void>((resolve, reject) => {
            $.ajax({
              url: `${server_url}/log-response`,
              method: "POST",
              data: JSON.stringify({ "campaign_id": campaign_id, "user_id": user_id, "payload": payload }),
              contentType: "application/json",
              dataType: "json",
              // TODO: handle being done
              success: (x) => resolve(),
              error: (XMLHttpRequest, textStatus, errorThrown) => {
                  console.error("Error storing data:", textStatus, errorThrown);
                  reject(`Status: ${XMLHttpRequest.status} Error: ${XMLHttpRequest.responseText}`);
              },
            });
          });
        } catch (e) {
          console.log("Error in try-catch:", e);
          notify(`Error storing item. <br> ${e} <br> Retrying in ${delay} seconds...`);
        }
      // wait for 5 seconds
      await new Promise(resolve => setTimeout(resolve, delay * 1000));
      delay *= 2
  }
}
package ja.src.main;
import java.net.*;

public class getTest {
    public static void main(String[] args) throws Exception {
        URL url = new URL("https://gr.sitea.cnfm.eot2.gic.ericsson.se/auth/v1");
        HttpURLConnection con = (HttpURLConnection) url.openConnection();
        con.setRequestMethod("POST");
        con.setRequestProperty("Content-Type", "application/json");
        con.setRequestProperty("X-login", "vnfm-user");
        con.setRequestProperty("X-password", "DefaultP12345!");
        int responseCode = con.getResponseCode();
        System.out.println("POST Response Code :: " + responseCode);
    }
}
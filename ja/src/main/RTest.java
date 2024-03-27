package ja.src.main;
import java.util.Hashtable;
import javax.naming.Context;

public class RTest {
    public static void main(String[] args) {
        final Hashtable<String, Object> env = new Hashtable<String, Object>();
        env.put(Context.REFERRAL, "follow");
        String referral = System.getenv("java.naming.referral");
        System.out.println("referral:  " + referral);
    }

}

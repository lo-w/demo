package ja.src.main;

import java.util.Date;
import java.util.Hashtable;
import javax.naming.ldap.LdapContext;
import javax.naming.ldap.InitialLdapContext;
import javax.naming.Context;
import javax.naming.directory.SearchControls;
import javax.naming.NamingEnumeration;
import javax.naming.directory.SearchResult;
import javax.naming.directory.Attributes;

public class LTest {
    public static void main(String[] args) throws Exception {
        System.out.println("run: " + new Date());
        LdapContext ldapContext = getLdapContext();
        SearchControls searchControls = getSearchControls();
        getResult(ldapContext, searchControls);
        System.out.println("done: " + new Date());
    }

    public static LdapContext getLdapContext() throws Exception {
        final Hashtable<String, Object> env = new Hashtable<String, Object>();
        env.put(Context.INITIAL_CONTEXT_FACTORY, "com.sun.jndi.ldap.LdapCtxFactory");
        env.put(Context.SECURITY_AUTHENTICATION, "simple");
        env.put(Context.PROVIDER_URL, "ldap://10.196.47.100:389");
        env.put(Context.SECURITY_PRINCIPAL, "cn=admin,dc=gic,dc=ericsson,dc=se");
        env.put(Context.SECURITY_CREDENTIALS, "ldapadmin");
        env.put(Context.REFERRAL, "follow");
        final LdapContext ctx = new InitialLdapContext(env, null);
        return ctx;
    }

    public static SearchControls getSearchControls() {
        SearchControls cons = new SearchControls();
        cons.setSearchScope(SearchControls.SUBTREE_SCOPE);
        String[] attrIDs = {"uid", "cn", "sn", "mail"};
        cons.setReturningAttributes(attrIDs);
        return cons;
    }

    public static void getResult(LdapContext ctx, SearchControls searchControls) throws Exception {
        try {
            NamingEnumeration<SearchResult> answer = ctx.search("dc=gic,dc=ericsson,dc=se", "(uid=john)", searchControls);
            if (answer.hasMore()) {
                Attributes attrs = answer.next().getAttributes();
                System.out.println("get user: " + attrs.get("cn"));
                System.out.println(attrs.get("uid"));
                System.out.println(attrs.get("cn"));
                System.out.println(attrs.get("sn"));
                System.out.println(attrs.get("mail"));
            } else {
                System.out.println("user not found.");
            }
        } catch (Exception ex) {
            ex.printStackTrace();
        }
    }
}
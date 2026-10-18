package service;
public class CompatibilityChecker {
    public static boolean isCompatible(String donor,String recipient){
        if(donor.equals("O-")) return true;
        if(donor.equals("O+")) return recipient.equals("O+")||recipient.equals("A+")||recipient.equals("B+")||recipient.equals("AB+");
        if(donor.equals("A-")) return recipient.equals("A-")||recipient.equals("A+")||recipient.equals("AB-")||recipient.equals("AB+");
        if(donor.equals("A+")) return recipient.equals("A+")||recipient.equals("AB+");
        if(donor.equals("B-")) return recipient.equals("B-")||recipient.equals("B+")||recipient.equals("AB-")||recipient.equals("AB+");
        if(donor.equals("B+")) return recipient.equals("B+")||recipient.equals("AB+");
        if(donor.equals("AB-")) return recipient.equals("AB-")||recipient.equals("AB+");
        if(donor.equals("AB+")) return recipient.equals("AB+");
        return false;
    }
}

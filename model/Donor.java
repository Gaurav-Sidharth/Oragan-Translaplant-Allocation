package model;
public class Donor {
    private final int donorId; private final String name; private final String bloodGroup;
    public Donor(int donorId,String name,String bloodGroup){this.donorId=donorId;this.name=name;this.bloodGroup=bloodGroup;}
    public int getDonorId(){return donorId;} public String getName(){return name;} public String getBloodGroup(){return bloodGroup;}
    public String toString(){return "Donor ID: "+donorId+", Name: "+name+", Blood Group: "+bloodGroup;}
}

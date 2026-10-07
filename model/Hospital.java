package model;
public class Hospital {
    private final int hospitalId; private final String name;
    public Hospital(int hospitalId,String name){this.hospitalId=hospitalId;this.name=name;}
    public int getHospitalId(){return hospitalId;} public String getName(){return name;}
    public String toString(){return hospitalId+" - "+name;}
}

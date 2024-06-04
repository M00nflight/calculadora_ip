import ipaddress
import tkinter as tk
from tkinter import messagebox, simpledialog

def calcular_prefijo_por_hosts(hosts_requeridos):
    for i in range(32, 0, -1):
        if (2 ** (32 - i) - 2) >= hosts_requeridos:
            return i
    return None

def obtener_siguiente_subred(base_red, prefijo_base, subredes_asignadas, hosts_requeridos):
    nuevo_prefijo = calcular_prefijo_por_hosts(hosts_requeridos)
    if (nuevo_prefijo is None) or (nuevo_prefijo < prefijo_base):
        return None

    red_base = ipaddress.IPv4Network(f"{base_red}/{prefijo_base}", strict=False)
    for subred in red_base.subnets(new_prefix=nuevo_prefijo):
        if all(not subred.overlaps(asignada) for asignada in subredes_asignadas):
            return subred
    return None

def direccion_a_binario(direccion, bits_host):
    partes = str(direccion).split('.')
    binario = ''.join(f"{int(octeto):08b}" for octeto in partes)
    return f"{binario[:32 - bits_host]} {binario[32 - bits_host:]}"

def calcular_subredes_por_hosts():
    Id_Red = simpledialog.askstring("Input", "Ingrese dirección de red y Prefijo (ej. 172.16.10.0/24):")
    
    if not Id_Red:
        return

    messagebox.showinfo("Nota", "Si necesita calcular varios host, Ingrese de MAYOR a MENOR\nFavor conservar buenas prácticas para óptimo funcionamiento :)")

    prefijo_base = int(Id_Red.split('/')[1])
    base_red = Id_Red.split('/')[0]
    subredes_asignadas = []

    while True:
        hosts_requeridos = simpledialog.askstring("Input", "Ingrese el número de hosts requeridos (o 0 para terminar):")
        if hosts_requeridos == "0":
            break

        hosts_requeridos = int(hosts_requeridos)
        subred = obtener_siguiente_subred(base_red, prefijo_base, subredes_asignadas, hosts_requeridos)

        if subred:
            subredes_asignadas.append(subred)

            nuevo_prefijo = subred.prefixlen
            bits_host = 32 - nuevo_prefijo

            network_bin = direccion_a_binario(subred.network_address, bits_host)
            first_host_bin = direccion_a_binario(subred.network_address + 1, bits_host)
            last_host_bin = direccion_a_binario(subred.broadcast_address - 1, bits_host)
            broadcast_bin = direccion_a_binario(subred.broadcast_address, bits_host)

            result = (
                f"\n{hosts_requeridos} host ({bits_host} bit)\n"
                f"Dirección de red: {subred.network_address} {network_bin.split()[1]} → .{subred.network_address.packed[-1]}\n"
                f"Primera Asignable: {subred.network_address + 1} {first_host_bin.split()[1]} → .{(subred.network_address + 1).packed[-1]}\n"
                f"Última Asignable: {subred.broadcast_address - 1} {last_host_bin.split()[1]} → .{(subred.broadcast_address - 1).packed[-1]}\n"
                f"Broadcast: {subred.broadcast_address} {broadcast_bin.split()[1]} → .{subred.broadcast_address.packed[-1]}\n"
                f"Máscara {prefijo_base} bit + {bits_host - (32 - prefijo_base)} bit → /{nuevo_prefijo} → {subred.netmask}"
            )
            messagebox.showinfo("Resultado", result)
        else:
            messagebox.showerror("Error", "No se pudieron asignar más subredes con la cantidad de hosts requeridos.")

    if subredes_asignadas:
        result = "\nSubredes asignadas:\n" + "\n".join(str(subred) for subred in subredes_asignadas)
        messagebox.showinfo("Subredes Asignadas", result)

# CALCULAR SUBREDES POR INTERFAZ ROUTER
def calcular_subredes_por_interfaces():
    network_address = simpledialog.askstring("Input", "Ingrese la dirección de red a distribuir (por ejemplo, 172.16.20.0/24):")
    interfaces_input = simpledialog.askstring("Input", "Ingrese las interfaces del router separadas por comas (por ejemplo, G0/0,G0/1):")
    interfaces = [iface.strip() for iface in interfaces_input.split(",") if iface.strip()]

    if not interfaces:
        messagebox.showerror("Error", "No se proporcionaron interfaces válidas.")
        return

    try:
        network = ipaddress.IPv4Network(network_address)
        if network.prefixlen > 30:
            messagebox.showerror("Error", "La red proporcionada no es válida. El prefijo debe ser menor o igual a 30.")
            return

        num_subnets = len(interfaces)
        new_prefixlen = network.prefixlen + 1
        while (2 ** (new_prefixlen - network.prefixlen) < num_subnets) and (new_prefixlen <= 30):
            new_prefixlen += 1

        if new_prefixlen > 30:
            messagebox.showerror("Error", "No es posible crear suficientes subredes con el prefijo dado.")
            return

        subnets = list(network.subnets(new_prefix=new_prefixlen))
        interface_subnet_map = {}

        for i, interface in enumerate(interfaces):
            if i < len(subnets):
                subnet = subnets[i]
                interface_subnet_map[interface] = subnet
            else:
                messagebox.showwarning("Advertencia", f"No hay suficientes subredes para asignar a la interfaz {interface}.")

        result = ""
        for interface, subnet in interface_subnet_map.items():
            result += (
                f"Interfaz {interface}:\n"
                f"  Subred: {subnet}\n"
                f"  Rango de direcciones: {subnet.network_address} - {subnet.broadcast_address}\n"
                f"  Primera dirección asignable: {subnet.network_address + 1}\n"
                f"  Última dirección asignable: {subnet.broadcast_address - 1}\n"
                f"  Dirección de broadcast: {subnet.broadcast_address}\n"
                f"  Máscara de subred: {subnet.netmask}\n\n"
            )
        messagebox.showinfo("Resultado", result)

    except ValueError as e:
        messagebox.showerror("Error", str(e))

def calcular_subredes_por_cantidad():
    base_red = simpledialog.askstring("Input", "Ingrese dirección de red y prefijo (ej. 192.168.10.0/24):")
    num_subredes = simpledialog.askinteger("Input", "Ingrese el número de subredes requeridas:")

    try:
        red_base = ipaddress.IPv4Network(base_red, strict=False)
    except ValueError as e:
        messagebox.showerror("Error", str(e))
        return

    nuevo_prefijo = red_base.prefixlen
    while (2 ** (nuevo_prefijo - red_base.prefixlen) < num_subredes) and (nuevo_prefijo <= 30):
        nuevo_prefijo += 1

    if nuevo_prefijo > 30:
        messagebox.showerror("Error", "No es posible crear suficientes subredes con el prefijo dado.")
        return

    subredes = list(red_base.subnets(new_prefix=nuevo_prefijo))[:num_subredes]

    result = ""
    for i, subred in enumerate(subredes):
        result += (
            f"\nSubred {i}:\n"
            f"  Dirección de red: {subred.network_address}\n"
            f"  Primera dirección asignable: {subred.network_address + 1}\n"
            f"  Última dirección asignable: {subred.broadcast_address - 1}\n"
            f"  Dirección de broadcast: {subred.broadcast_address}\n"
            f"  Máscara de subred: {subred.netmask}\n"
            f"  Total de direcciones IP válidas o usables: {subred.num_addresses - 2}\n"
        )
    messagebox.showinfo("Resultado", result)

def main():
    root = tk.Tk()
    root.title("Calculadora de Subredes")

    label = tk.Label(root, text="Seleccione una opción:")
    label.pack()

    button1 = tk.Button(root, text="Calcular subredes según la cantidad de hosts requeridos", command=calcular_subredes_por_hosts)
    button1.pack()

    button2 = tk.Button(root, text="Calcular subredes para las interfaces del router", command=calcular_subredes_por_interfaces)
    button2.pack()

    button3 = tk.Button(root, text="Calcular subred según SR requeridas (TOTAL)", command=calcular_subredes_por_cantidad)
    button3.pack()

    button_exit = tk.Button(root, text="Salir", command=root.quit)
    button_exit.pack()

    root.mainloop()

if __name__ == "__main__":
    main()
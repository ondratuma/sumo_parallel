step = 255.0/100.0
for i in range(101):
    if i == 0:
        red = green = blue = str(150)
    elif i == 100:
        blue = str(0)
        green = str(0)
        red = str(255)
    else:
        red = str(2*i * step)
        green = str(2*(255 - i*step) )
        blue = str(0)
        red = str(min(255,int(float(red))))
        green = str(min(255,int(float(green))))
        blue = str(min(255,int(float(blue))))
    print ("<entry color=\"" + red +"," + green + "," + blue + "\" threshold=\"" + str(i) + ".00\"/>")